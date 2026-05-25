from pydantic import BaseModel
from typing import Optional

class Location(BaseModel):
    latitude: float
    longitude: float

class Address(BaseModel):
    street: str
    city: str
    state: str
    postal_code: str
    location: Location # Nested Location model

class BookingRequest(BaseModel):
    user_id: str
    pickup_address: Address
    drop_address: Address

class BookingResponse(BaseModel):
    booking_id: str
    user_id: str
    pickup_address: Address
    drop_address: Address
    price_usd: float
    driver_id: Optional[str] = None # Driver might not be found immediately
    status: str # E.g., "CONFIRMED", "PENDING", "FAILED"

class HealthCheckResponse(BaseModel):
    status: str