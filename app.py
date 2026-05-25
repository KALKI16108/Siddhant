from fastapi import FastAPI, HTTPException
import uuid # For generating unique booking IDs
from schemas import BookingRequest, BookingResponse, HealthCheckResponse, Address, Location
from pricing import calculate_price
from matching import find_nearest_driver

# Initialize the FastAPI application
app = FastAPI(
    title="Ride Booking API",
    description="A simplified FastAPI service for booking rides.",
    version="1.0.0"
)

@app.get("/", response_model=HealthCheckResponse, summary="Health Check")
async def health_check():
    """
    Provides a simple health check endpoint to confirm the API is operational.
    """
    return {"status": "Sync engine live"}

@app.post("/book", response_model=BookingResponse, status_code=200, summary="Book a Ride")
async def book_ride(request: BookingRequest):
    """
    Handles the ride booking process:
    1. Validates the request payload using Pydantic models.
    2. Calculates the ride price based on pickup and drop-off locations.
    3. Attempts to find an available driver.
    4. Generates a unique booking ID and confirms the booking.
    5. Returns a detailed booking confirmation.
    """
    # Extract locations from the request
    pickup_loc = request.pickup_address.location
    drop_loc = request.drop_address.location

    # 1. Calculate Price
    calculated_price = calculate_price(pickup_loc, drop_loc)

    # 2. Find Driver
    driver_id = find_nearest_driver(pickup_loc)

    # If no driver is found, raise an HTTP exception
    if not driver_id:
        raise HTTPException(
            status_code=503, # Service Unavailable
            detail="No drivers available at this time. Please try again later."
        )

    # 3. Generate Booking ID and set status
    booking_id = str(uuid.uuid4()) # Generate a unique UUID for the booking
    booking_status = "CONFIRMED" # For this simplified example, assume immediate confirmation

    # 4. Construct and return the BookingResponse
    return BookingResponse(
        booking_id=booking_id,
        user_id=request.user_id,
        pickup_address=request.pickup_address,
        drop_address=request.drop_address,
        price_usd=calculated_price,
        driver_id=driver_id,
        status=booking_status
    )