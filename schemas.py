from pydantic import BaseModel
from typing import Optional

# Base model for driver location updates
class DriverLocationUpdate(BaseModel):
    driver_id: str
    latitude: float
    longitude: float

# Base model for driver status updates
class DriverStatusUpdate(BaseModel):
    driver_id: str
    is_active: bool  # True for On Duty, False for Off Duty

# Response model for order tracking
class OrderTrackingResponse(BaseModel):
    booking_id: str
    user_id: str
    status: str  # e.g., 'pending', 'accepted', 'en_route', 'completed', 'cancelled'
    pickup_latitude: float
    pickup_longitude: float
    dropoff_latitude: float
    dropoff_longitude: float
    driver_id: Optional[str] = None
    driver_latitude: Optional[float] = None
    driver_longitude: Optional[float] = None
    eta_minutes: Optional[float] = None # Estimated Time of Arrival for the driver to reach pickup location