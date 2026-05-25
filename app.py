import uuid
import datetime
import httpx
from fastapi import FastAPI, status, HTTPException
from typing import List, Dict, Optional

from schemas import (
    Location, Address, BookingRequest, Driver, PricingResponse, BookingResponse
)
from pricing import calculate_fare
from matching import haversine_distance, find_nearby_drivers

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Intra-City Courier & Delivery Backend",
    description="Production-ready backend engine for hyper-local logistics in Mumbai, "
                "competing with platforms like Borzo and Porter."
)

# --- Configuration Constants ---
OSRM_BASE_URL = "http://router.project-osrm.org/route/v1/driving/"
OSRM_TIMEOUT_SECONDS = 5
WINDING_ROAD_SCALE_FACTOR = 1.30 # Adds 30% to straight-line distance for realism if OSRM fails
AVERAGE_DELIVERY_SPEED_KMH = 25.0 # Used for estimated_time_minutes when OSRM fails

# --- In-Memory Driver Database (Simulated for testing) ---
# Drivers distributed across key Mumbai transit nodes with varying wallet balances.
DRIVERS_DB: List[Driver] = [
    Driver(id=str(uuid.uuid4()), name="Ravi Sharma", current_location=Location(latitude=19.0760, longitude=72.8777), wallet_balance=150.75), # CST area
    Driver(id=str(uuid.uuid4()), name="Priya Singh", current_location=Location(latitude=19.0896, longitude=72.8631), wallet_balance=5.50), # Dadar West (below min balance)
    Driver(id=str(uuid.uuid4()), name="Amit Patel", current_location=Location(latitude=19.0607, longitude=72.8306), wallet_balance=200.00), # Bandra West
    Driver(id=str(uuid.uuid4()), name="Sneha Rao", current_location=Location(latitude=19.0538, longitude=72.9094), wallet_balance=80.25), # Kurla
    Driver(id=str(uuid.uuid4()), name="Vikas Gupta", current_location=Location(latitude=18.9958, longitude=72.8188), wallet_balance=15.00), # Lower Parel (below min balance)
    Driver(id=str(uuid.uuid4()), name="Anjali Desai", current_location=Location(latitude=19.1233, longitude=72.8596), wallet_balance=120.00), # Andheri East
    Driver(id=str(uuid.uuid4()), name="Kiran Yadav", current_location=Location(latitude=19.0435, longitude=72.8105), wallet_balance=60.00), # Mahim
    Driver(id=str(uuid.uuid4()), name="Rajesh Kumar", current_location=Location(latitude=19.0069, longitude=72.8290), wallet_balance=25.00), # Worli (just above min balance)
    Driver(id=str(uuid.uuid4()), name="Meera Soni", current_location=Location(latitude=19.1501, longitude=72.8468), wallet_balance=180.50), # Goregaon
    Driver(id=str(uuid.uuid4()), name="Suresh Iyer", current_location=Location(latitude=19.0818, longitude=72.8809), wallet_balance=30.00)  # BKC (in a traffic zone)
]

# --- Utility Function: OSRM Routing Client with Fallback ---
async def get_route_details(
    start_loc: Location,
    end_loc: Location
) -> Dict[str, float]:
    """
    Fetches road network distance and time from OSRM. If OSRM fails or times out,
    it falls back to Haversine straight-line distance with a winding road scale factor.

    Args:
        start_loc: The starting geographical location.
        end_loc: The ending geographical location.

    Returns:
        A dictionary containing 'distance_km' and 'estimated_time_minutes',
        both rounded to two decimal places.
    """
    client = httpx.AsyncClient()
    
    # OSRM requires coordinates in `longitude,latitude` format
    start_coords_str = f"{start_loc.longitude},{start_loc.latitude}"
    end_coords_str = f"{end_loc.longitude},{end_loc.latitude}"
    osrm_url = f"{OSRM_BASE_URL}{start_coords_str};{end_coords_str}"

    distance_km: float
    estimated_time_minutes: float

    try:
        response = await client.get(osrm_url, timeout=OSRM_TIMEOUT_SECONDS)
        response.raise_for_status() # Raise an exception for 4xx or 5xx responses
        data = response.json()

        if data and data['routes']:
            route = data['routes'][0]
            distance_km = route['distance'] / 1000  # OSRM returns distance in meters
            estimated_time_minutes = route['duration'] / 60 # OSRM returns duration in seconds
            print(f"OSRM successful: Distance={distance_km:.2f}km, Time={estimated_time_minutes:.2f}min")
        else:
            raise ValueError("OSRM response did not contain valid routes.")

    except (httpx.RequestError, httpx.HTTPStatusError, ValueError) as e:
        # Fallback to Haversine calculation if OSRM fails or returns no routes
        print(f"OSRM routing failed or timed out ({type(e).__name__}: {e}). Falling back to Haversine calculation.")
        straight_line_distance = haversine_distance(
            start_loc.latitude, start_loc.longitude,
            end_loc.latitude, end_loc.longitude
        )
        distance_km = straight_line_distance * WINDING_ROAD_SCALE_FACTOR
        estimated_time_minutes = (distance_km / AVERAGE_DELIVERY_SPEED_KMH) * 60
        print(f"Fallback Haversine: Distance={distance_km:.2f}km, Time={estimated_time_minutes:.2f}min")

    finally:
        await client.aclose()
    
    return {
        "distance_km": round(distance_km, 2),
        "estimated_time_minutes": round(estimated_time_minutes, 2)
    }

# --- FastAPI Endpoints ---

@app.get("/", summary="API Health Check", response_model=Dict[str, str])
async def health_check():
    """
    Simple health check endpoint to verify that the API is running.
    """
    return {"status": "ok", "message": "Intra-City Courier Backend is running!"}

@app.post("/price", response_model=PricingResponse, summary="Get a price quote for a delivery")
async def get_price_quote(request: BookingRequest):
    """
    Calculates the estimated fare for a delivery request based on real-road distance
    (or fallback straight-line), estimated time, and applies any applicable surcharges.
    """
    route_details = await get_route_details(request.pickup_address.location, request.drop_address.location)
    distance_km = route_details["distance_km"]
    estimated_time_minutes = route_details["estimated_time_minutes"]

    # Use current local time for surcharge evaluation.
    # For a production system deployed globally, proper timezone handling (e.g., pytz/zoneinfo for IST)
    # would be crucial, but for a Mumbai-centric context and simplicity as per prompt,
    # datetime.datetime.now() assumes the server's local time is appropriate or acceptable.
    current_time_for_surcharge_check = datetime.datetime.now()

    fare_components = calculate_fare(
        distance_km=distance_km,
        pickup_text=request.pickup_address.street,
        drop_text=request.drop_address.street,
        evaluation_timestamp=current_time_for_surcharge_check
    )

    return PricingResponse(
        total_fare=fare_components["total_fare"],
        base_fare=fare_components["base_fare"],
        per_km_fare=fare_components["per_km_fare"],
        surcharge=fare_components["surcharge"],
        distance_km=distance_km,
        estimated_time_minutes=estimated_time_minutes
    )

@app.post("/book", response_model=BookingResponse, summary="Book a delivery and assign a driver")
async def book_delivery(request: BookingRequest):
    """
    Orchestrates the booking process: calculates fare, finds eligible drivers,
    assigns the closest candidate, and issues a final booking response.
    """
    # 1. Get route details (distance and time)
    route_details = await get_route_details(request.pickup_address.location, request.drop_address.location)
    distance_km = route_details["distance_km"]
    estimated_time_minutes = route_details["estimated_time_minutes"]

    # 2. Calculate fare based on route details and current time
    current_time_for_surcharge_check = datetime.datetime.now()

    fare_components = calculate_fare(
        distance_km=distance_km,
        pickup_text=request.pickup_address.street,
        drop_text=request.drop_address.street,
        evaluation_timestamp=current_time_for_surcharge_check
    )

    pricing_response = PricingResponse(
        total_fare=fare_components["total_fare"],
        base_fare=fare_components["base_fare"],
        per_km_fare=fare_components["per_km_fare"],
        surcharge=fare_components["surcharge"],
        distance_km=distance_km,
        estimated_time_minutes=estimated_time_minutes
    )

    # 3. Find nearby and eligible drivers
    nearby_eligible_drivers = find_nearby_drivers(
        pickup_location=request.pickup_address.location,
        driver_list=DRIVERS_DB # Using the in-memory simulated database
    )

    assigned_driver_id: Optional[str] = None
    booking_status: str
    booking_message: str

    if nearby_eligible_drivers:
        # Assign the closest eligible driver
        closest_driver_info = nearby_eligible_drivers[0]
        assigned_driver_id = closest_driver_info["driver"].id
        booking_status = "ASSIGNED"
        booking_message = (
            f"Booking confirmed. Driver {closest_driver_info['driver'].name} "
            f"({assigned_driver_id}) assigned. "
            f"Estimated pickup ETA: {closest_driver_info['estimated_pickup_eta_minutes']:.2f} minutes."
        )
        print(f"Booking {request.user_id} assigned to driver {assigned_driver_id}")
        # In a real system, further actions like updating driver status, notifying driver/user,
        # persisting booking to a database, etc., would occur here.
    else:
        booking_status = "NO_DRIVER_FOUND"
        booking_message = "No available drivers found within the service radius or with sufficient wallet balance."
        print(f"No driver found for booking request by user {request.user_id}")


    # 4. Return finalized BookingResponse
    return BookingResponse(
        booking_id=str(uuid.uuid4()), # Generate a unique ID for the booking
        user_id=request.user_id,
        fare=pricing_response,
        driver_id=assigned_driver_id,
        status=booking_status,
        message=booking_message
    )