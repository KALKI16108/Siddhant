from pydantic import BaseModel
from typing import Tuple, List

class Coordinates(BaseModel):
    """Represents geographical coordinates."""
    latitude: float
    longitude: float

class BookingRequest(BaseModel):
    """Schema for the incoming booking request."""
    user_id: str
    pickup_point: Coordinates
    dropoff_point: Coordinates

class BookingResponse(BaseModel):
    """Schema for the outgoing booking response."""
    total_fare: float
    driver_name: str
    status: str
    # You could add more fields here like:
    # estimated_eta: int # in minutes
    # driver_location: Coordinates
    # route_points: List[Coordinates]