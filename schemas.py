from pydantic import BaseModel, Field
from typing import Optional

# --- User Authentication Schemas ---

class UserBase(BaseModel):
    username: str = Field(..., example="johndoe")

class UserCreate(UserBase):
    password: str = Field(..., example="strong-password-123")

class UserInDB(UserBase):
    id: int
    hashed_password: str

    class Config:
        from_attributes = True # updated from orm_mode = True for Pydantic v2

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None

# --- Delivery Service Schemas (Integrated with Auth) ---

class DeliveryRequest(BaseModel):
    origin: str = Field(..., example="123 Main St, Anytown")
    destination: str = Field(..., example="456 Oak Ave, Anycity")
    weight_kg: float = Field(..., gt=0, example=5.5)
    dimensions_cm: list[float] = Field(..., min_length=3, max_length=3, example=[20.0, 15.0, 10.0]) # [length, width, height]

class DeliveryPrice(BaseModel):
    amount: float = Field(..., gt=0, example=15.75)
    currency: str = Field(default="USD", example="USD")
    estimated_duration_minutes: int = Field(..., gt=0, example=60)

class DeliveryMatch(BaseModel):
    driver_id: str = Field(..., example="DRV001")
    estimated_pickup_time_minutes: int = Field(..., gt=0, example=15)
    estimated_delivery_time_minutes: int = Field(..., gt=0, example=75)
    driver_name: str = Field(..., example="Alice Smith")
    driver_phone: str = Field(..., example="+15551234567")

class DeliveryConfirmation(BaseModel):
    delivery_id: str = Field(..., example="DEL12345")
    status: str = Field(default="booked", example="booked")
    message: str = Field(default="Delivery successfully booked!", example="Delivery successfully booked!")