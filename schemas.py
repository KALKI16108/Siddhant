from pydantic import BaseModel, Field
from typing import Optional

class Location(BaseModel):
    """
    Pydantic model for geographical coordinates.
    Latitude must be between -90 and 90, longitude between -180 and 180.
    """
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")

class Address(BaseModel):
    """
    Pydantic model for a full address, including street, city, state, postal code,
    and geographical location.
    """
    street: str = Field(..., min_length=1, description="Street address")
    city: str = Field(..., min_length=1, description="City name")
    state: str = Field(..., min_length=1, description="State name")
    postal_code: str = Field(..., min_length=1, description="Postal code")
    location: Location = Field(..., description="Geographical coordinates of the address")

class BookingRequest(BaseModel):
    """
    Pydantic model for a user's delivery booking request.
    Includes user ID, pickup address, and drop-off address.
    """
    user_id: str = Field(..., min_length=1, description="Unique identifier for the user")
    pickup_address: Address = Field(..., description="Details of the pickup address")
    drop_address: Address = Field(..., description="Details of the drop-off address")

class Driver(BaseModel):
    """
    Pydantic model for a driver's profile, including ID, name, current location,
    and wallet balance.
    """
    id: str = Field(..., min_length=1, description="Unique identifier for the driver")
    name: str = Field(..., min_length=1, description="Name of the driver")
    current_location: Location = Field(..., description="Driver's current geographical location")
    wallet_balance: float = Field(..., ge=0, description="Driver's current wallet balance")

class PricingResponse(BaseModel):
    """
    Pydantic model for the detailed pricing breakdown of a delivery.
    """
    total_fare: float = Field(..., ge=0, description="Total calculated fare")
    base_fare: float = Field(..., ge=0, description="Base fare component")
    per_km_fare: float = Field(..., ge=0, description="Per kilometer fare component")
    surcharge: float = Field(..., ge=0, description="Applicable surcharges (e.g., traffic)")
    distance_km: float = Field(..., ge=0, description="Estimated total distance for delivery in kilometers")
    estimated_time_minutes: float = Field(..., ge=0, description="Estimated total time for delivery in minutes")

class BookingResponse(BaseModel):
    """
    Pydantic model for the response after a booking attempt.
    Includes booking ID, user ID, fare details, assigned driver ID (if any),
    status, and a message.
    """
    booking_id: str = Field(..., description="Unique identifier for the confirmed booking")
    user_id: str = Field(..., description="Unique identifier of the user who made the booking")
    fare: PricingResponse = Field(..., description="Detailed fare information for the booking")
    driver_id: Optional[str] = Field(None, description="ID of the assigned driver, if any")
    status: str = Field(..., description="Status of the booking (e.g., ASSIGNED, NO_DRIVER_FOUND)")
    message: str = Field(..., description="A descriptive message about the booking status")