```python
# /app/sync-workspace-Siddhant/schemas.py
from pydantic import BaseModel, Field, confloat
from typing import Optional, List


class Location(BaseModel):
    latitude: confloat(ge=-90, le=90)
    longitude: confloat(ge=-180, le=180)


class Address(BaseModel):
    street: str
    city: str
    state: str
    postal_code: str
    location: Location


class BookingRequest(BaseModel):
    user_id: str
    pickup_address: Address
    drop_address: Address


class Driver(BaseModel):
    id: str
    name: str
    current_location: Location
    wallet_balance: float


class PricingResponse(BaseModel):
    total_fare: float
    base_fare: float
    per_km_fare: float
    surcharge: float
    distance_km: float
    estimated_time_minutes: float


class BookingResponse(BaseModel):
    booking_id: str
    user_id: str
    fare: PricingResponse
    driver_id: Optional[str]
    status: str
    message: str

```
```python
# /app/sync-workspace-Siddhant/pricing.py
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

# Pricing Constants
BASE_FARE_FLAT = Decimal('45.00')
BASE_FARE_KM_THRESHOLD = Decimal('2.00')
PER_KM_RATE = Decimal('8.00')
TRAFFIC_SURCHARGE = Decimal('20.00')

# Traffic Surcharge Keywords and Time
TRAFFIC_KEYWORDS = ['bkc', 'bandra kurla complex', 'saki naka', 'lower parel']
TRAFFIC_START_HOUR = 17  # 5 PM
TRAFFIC_END_HOUR = 20    # 8 PM


def calculate_fare(distance_km: float, pickup_text: str, drop_text: str, execution_time: datetime) -> dict:
    """
    Calculates the total fare based on distance, traffic conditions, and time.

    Args:
        distance_km: The distance of the trip in kilometers.
        pickup_text: The text description of the pickup address.
        drop_text: The text description of the drop-off address.
        execution_time: The datetime object when the fare calculation is performed.

    Returns:
        A dictionary containing fare breakdown (total_fare, base_fare, per_km_fare, surcharge).
    """
    distance_decimal = Decimal(str(distance_km))
    
    current_base_fare = Decimal('0.00')
    current_per_km_fare = Decimal('0.00')
    current_surcharge = Decimal('0.00')

    # 1. Base Fare and Per KM Rate
    if distance_decimal <= BASE_FARE_KM_THRESHOLD:
        current_base_fare = BASE_FARE_FLAT
    else:
        current_base_fare = BASE_FARE_FLAT
        remaining_distance = distance_decimal - BASE_FARE_KM_THRESHOLD
        current_per_km_fare = remaining_distance * PER_KM_RATE

    # 2. Traffic Surcharge
    is_peak_hour = TRAFFIC_START_HOUR <= execution_time.hour < TRAFFIC_END_HOUR
    
    pickup_text_lower = pickup_text.lower()
    drop_text_lower = drop_text.lower()
    
    is_choke_point = any(keyword in pickup_text_lower or keyword in drop_text_lower for keyword in TRAFFIC_KEYWORDS)

    if is_peak_hour and is_choke_point:
        current_surcharge = TRAFFIC_SURCHARGE

    total_fare = current_base_fare + current_per_km_fare + current_surcharge

    # Round all Decimal values to two decimal places
    total_fare_rounded = float(total_fare.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    base_fare_rounded = float(current_base_fare.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    per_km_fare_rounded = float(current_per_km_fare.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    surcharge_rounded = float(current_surcharge.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

    return {
        "total_fare": total_fare_rounded,
        "base_fare": base_fare_rounded,
        "per_km_fare": per_km_fare_rounded,
        "surcharge": surcharge_rounded,
    }

```
```python
# /app/sync-workspace-Siddhant/matching.py
import math
from typing import List, Dict
from schemas import Location, Driver

# Constants
EARTH_RADIUS_KM = 6371  # Radius of Earth in kilometers
MIN_DRIVER_WALLET_BALANCE = 20.0
DRIVER_MATCHING_RADIUS_KM = 5.0
DRIVER_PICKUP_AVG_SPEED_KMH = 20.0


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the Haversine distance between two sets of latitude and longitude coordinates.

    Args:
        lat1 (float): Latitude of the first point.
        lon1 (float): Longitude of the first point.
        lat2 (float): Latitude of the second point.
        lon2 (float): Longitude of the second point.

    Returns:
        float: The distance between the two points in kilometers.
    """
    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Haversine formula
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = EARTH_RADIUS_KM * c
    return distance


def find_nearby_drivers(pickup_location: Location, driver_list: List[Driver]) -> List[Dict]:
    """
    Filters drivers based on wallet balance, proximity to pickup location,
    calculates estimated pickup ETA, and sorts them by distance.

    Args:
        pickup_location (Location): The pickup location for the booking.
        driver_list (List[Driver]): A list of all available drivers.

    Returns:
        List[Dict]: A list of dictionaries, each containing driver_id, distance_to_pickup_km,
                    and estimated_pickup_eta_minutes, sorted by distance.
    """
    eligible_drivers = []

    for driver in driver_list:
        # 1. Financial Gatekeeper: Filter out drivers with insufficient wallet balance
        if driver.wallet_balance < MIN_DRIVER_WALLET_BALANCE:
            continue

        # 2. Matching Engine: Find available drivers within a strict 5.0-kilometer radius
        distance_to_pickup_km = haversine_distance(
            pickup_location.latitude, pickup_location.longitude,
            driver.current_location.latitude, driver.current_location.longitude
        )

        if distance_to_pickup_km <= DRIVER_MATCHING_RADIUS_KM:
            # Compute an estimated pickup ETA
            estimated_pickup_eta_minutes = (distance_to_pickup_km / DRIVER_PICKUP_AVG_SPEED_KMH) * 60

            eligible_drivers.append({
                "driver_id": driver.id,
                "distance_to_pickup_km": round(distance_to_pickup_km, 2),
                "estimated_pickup_eta_minutes": round(estimated_pickup_eta_minutes, 2),
                "driver_name": driver.name, # Added for completeness, might be useful in logs
                "driver_location": driver.current_location # Added for completeness
            })

    # Sort the matched drivers by distance (closest-first)
    eligible_drivers.sort(key=lambda x: x["distance_to_pickup_km"])

    return eligible_drivers

```
```python
# /app/sync-workspace-Siddhant/app.py
from fastapi import FastAPI, HTTPException, status
from typing import List, Optional
from datetime import datetime
import httpx
import uuid
import asyncio

from schemas import (
    Location, Address, BookingRequest, Driver,
    PricingResponse, BookingResponse
)
from pricing import calculate_fare
from matching import haversine_distance, find_nearby_drivers

# Initialize FastAPI app
app = FastAPI(
    title="Intra-City Courier & Delivery Platform",
    description="Backend engine for a Borzo/Porter-like service in Mumbai.",
    version="1.0.0",
)

# Constants
OSRM_BASE_URL = "http://router.project-osrm.org/route/v1/driving/"
ROUTE_FALLBACK_AVG_SPEED_KMH = 25.0  # Average speed for route duration estimation if OSRM fails
WINDING_ROAD_COEFFICIENT = 1.3       # 30% winding-road scale coefficient for Haversine fallback

# In-memory seed list of simulated Mumbai drivers
# (Lat/Lon values are rough estimates for Mumbai locations)
drivers_db: List[Driver] = [
    Driver(id="DRV001", name="Rajesh Kumar", current_location=Location(latitude=19.0760, longitude=72.8777), wallet_balance=150.75),  # Dadar
    Driver(id="DRV002", name="Priya Sharma", current_location=Location(latitude=19.0517, longitude=72.8290), wallet_balance=80.20),   # Bandra West
    Driver(id="DRV003", name="Amit Singh", current_location=Location(latitude=19.0664, longitude=72.8948), wallet_balance=10.00),   # Kurla (low balance)
    Driver(id="DRV004", name="Sonia Das", current_location=Location(latitude=18.9400, longitude=72.8347), wallet_balance=200.50),  # CST
    Driver(id="DRV005", name="Kiran Yadav", current_location=Location(latitude=18.9959, longitude=72.8259), wallet_balance=50.00),   # Lower Parel
    Driver(id="DRV006", name="Vikram Gupta", current_location=Location(latitude=19.0760, longitude=72.8777), wallet_balance=30.00),  # Dadar
    Driver(id="DRV007", name="Meera Patel", current_location=Location(latitude=19.0605, longitude=72.8596), wallet_balance=120.00), # BKC
    Driver(id="DRV008", name="Rahul Jain", current_location=Location(latitude=19.1170, longitude=72.8466), wallet_balance=25.00),   # Saki Naka
    Driver(id="DRV009", name="Deepa Menon", current_location=Location(latitude=19.0068, longitude=72.8247), wallet_balance=70.00),   # Worli
    Driver(id="DRV010", name="Suresh Kadam", current_location=Location(latitude=19.1213, longitude=72.8491), wallet_balance=15.00),   # Andheri (low balance)
]


async def get_route_data(
    pickup_loc: Location, drop_loc: Location
) -> tuple[float, float]:
    """
    Fetches real road network distance and estimated time from OSRM,
    with an automated fallback to Haversine calculation + winding-road coefficient.

    Returns:
        tuple[float, float]: (distance_km, estimated_time_minutes)
    """
    osrm_url = (
        f"{OSRM_BASE_URL}"
        f"{pickup_loc.longitude},{pickup_loc.latitude};"
        f"{drop_loc.longitude},{drop_loc.latitude}"
        f"?overview=false"
    )

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:  # 3-second timeout
            response = await client.get(osrm_url)
            response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes

            data = response.json()
            if data and data.get("routes"):
                route = data["routes"][0]
                distance_meters = route["distance"]
                duration_seconds = route["duration"]
                return distance_meters / 1000, duration_seconds / 60
            else:
                raise ValueError("No routes found in OSRM response.")

    except (httpx.RequestError, httpx.HTTPStatusError, ValueError, asyncio.TimeoutError) as e:
        print(f"OSRM request failed or timed out: {e}. Falling back to Haversine calculation.")
        # Fallback: Haversine distance with winding-road coefficient
        straight_line_distance_km = haversine_distance(
            pickup_loc.latitude, pickup_loc.longitude,
            drop_loc.latitude, drop_loc.longitude
        )
        distance_km = straight_line_distance_km * WINDING_ROAD_COEFFICIENT
        estimated_time_minutes = (distance_km / ROUTE_FALLBACK_AVG_SPEED_KMH) * 60
        return distance_km, estimated_time_minutes


@app.get("/", summary="API Health Check")
async def health_check():
    """
    Returns a simple message to indicate the API is running.
    """
    return {"status": "ok", "message": "Courier backend is up and running!"}


@app.post("/price", response_model=PricingResponse, summary="Get a price quote for a booking")
async def get_price(request: BookingRequest):
    """
    Calculates and returns a detailed price quote for a given pickup and drop-off.
    """
    pickup_loc = request.pickup_address.location
    drop_loc = request.drop_address.location

    distance_km, estimated_time_minutes = await get_route_data(pickup_loc, drop_loc)
    
    fare_details = calculate_fare(
        distance_km=distance_km,
        pickup_text=request.pickup_address.street,
        drop_text=request.drop_address.street,
        execution_time=datetime.now()
    )

    return PricingResponse(
        total_fare=fare_details["total_fare"],
        base_fare=fare_details["base_fare"],
        per_km_fare=fare_details["per_km_fare"],
        surcharge=fare_details["surcharge"],
        distance_km=round(distance_km, 2),
        estimated_time_minutes=round(estimated_time_minutes, 2),
    )


@app.post("/book", response_model=BookingResponse, summary="Create a new booking and assign a driver")
async def create_booking(request: BookingRequest):
    """
    Orchestrates pricing calculation, live driver matching, driver assignment,
    and returns a finalized booking response.
    """
    pickup_loc = request.pickup_address.location
    drop_loc = request.drop_address.location

    distance_km, estimated_time_minutes = await get_route_data(pickup_loc, drop_loc)

    fare_details = calculate_fare(
        distance_km=distance_km,
        pickup_text=request.pickup_address.street,
        drop_text=request.drop_address.street,
        execution_time=datetime.now()
    )

    # Prepare PricingResponse for the final booking object
    pricing_response = PricingResponse(
        total_fare=fare_details["total_fare"],
        base_fare=fare_details["base_fare"],
        per_km_fare=fare_details["per_km_fare"],
        surcharge=fare_details["surcharge"],
        distance_km=round(distance_km, 2),
        estimated_time_minutes=round(estimated_time_minutes, 2),
    )

    # Find nearby drivers
    nearby_drivers_info = find_nearby_drivers(pickup_loc, drivers_db)

    assigned_driver_id: Optional[str] = None
    booking_status: str = "failed"
    message: str = "No suitable drivers found for this booking."

    if nearby_drivers_info:
        # Assign the closest driver
        closest_driver = nearby_drivers_info[0]
        assigned_driver_id = closest_driver["driver_id"]
        booking_status = "pending_driver_acceptance"
        message = f"Booking created. Driver {closest_driver['driver_name']} ({assigned_driver_id}) is on the way."

        # Simulate deducting from driver wallet or updating driver status here if this was a persistent DB
        # For this in-memory example, we just assign.

    return BookingResponse(
        booking_id=str(uuid.uuid4()),
        user_id=request.user_id,
        fare=pricing_response,
        driver_id=assigned_driver_id,
        status=booking_status,
        message=message,
    )

```