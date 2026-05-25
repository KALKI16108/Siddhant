from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid

# Pydantic schemas for data validation and serialization

class UserBase(BaseModel):
    name: str = Field(..., example="Alice Smith")

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True # Allow ORM models to be converted to Pydantic

class DriverBase(BaseModel):
    name: str = Field(..., example="Bob Johnson")
    latitude: float = Field(..., example=34.0522)
    longitude: float = Field(..., example=-118.2437)
    wallet_balance: float = Field(0.0, ge=0, example=50.75)
    is_active: bool = Field(True, example=True)

class DriverCreate(DriverBase):
    pass

class DriverResponse(DriverBase):
    id: uuid.UUID

    class Config:
        from_attributes = True

class BookingRequest(BaseModel):
    user_id: uuid.UUID = Field(..., example=str(uuid.uuid4()))
    pickup_latitude: float = Field(..., example=34.0522)
    pickup_longitude: float = Field(..., example=-118.2437)
    drop_latitude: float = Field(..., example=34.0000)
    drop_longitude: float = Field(..., example=-118.1000)
    pickup_address: str = Field(..., example="123 Main St, Los Angeles")
    drop_address: str = Field(..., example="456 Oak Ave, Los Angeles")

class BookingResponse(BaseModel):
    booking_id: uuid.UUID
    user_id: uuid.UUID
    driver_id: Optional[uuid.UUID] = None
    total_fare: float
    status: str
    pickup_address: str
    drop_address: str
    created_at: datetime

    class Config:
        from_attributes = True