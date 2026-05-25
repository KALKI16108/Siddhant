Here's the refactored application, transitioning from in-memory arrays to a robust relational database layer using SQLAlchemy and PostgreSQL, configured for Supabase.

I've structured the application into several modules:
*   `database.py`: Handles the database connection and session management.
*   `models.py`: Defines the SQLAlchemy ORM models for our tables. This replaces the conceptual 'schemas.py' for database schema definition.
*   `schemas.py`: Defines Pydantic schemas for request and response data validation.
*   `pricing.py`: Contains logic for calculating the fare.
*   `matching.py`: Contains logic for driver matching, including haversine distance calculation.
*   `app.py`: The main FastAPI application, integrating all components.

---

File Name: database.py
```python
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load environment variables from .env file for local development
load_dotenv()

# Safely read DATABASE_URL from environment secrets
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set.")

# Initialize SQLAlchemy Engine
# The `connect_args` might be needed for some specific database setups,
# but usually not required for standard Supabase connections with psycopg2.
# For Supabase, the URL typically includes SSL parameters if needed, or it's handled automatically.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True # Ensures connections are valid
)

# Create a SessionLocal class
# Each instance of the SessionLocal class will be a database session.
# The `autocommit=False` means that we have to explicitly commit our changes,
# which is good practice for transactions.
# The `autoflush=False` means that ORM operations won't flush to the database automatically
# until a commit or an explicit flush.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declare a Base for our declarative models
# This will be imported by our models.py to define table structures.
Base = declarative_base()

def get_db():
    """
    Dependency to provide a database session for FastAPI endpoints.
    It ensures the session is closed after the request is processed.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Example: Function to create all tables (for initial setup/migrations)
def create_db_and_tables():
    """
    Creates all defined tables in the database.
    This should typically be part of a migration strategy (e.g., Alembic),
    but for a simple setup, it can be run manually or on application startup.
    """
    # Import models to ensure Base knows about them before creating tables
    # pylint: disable=unused-import,import-outside-toplevel
    from . import models
    Base.metadata.create_all(bind=engine)
    print("Database tables created (if they didn't exist).")

if __name__ == '__main__':
    # This block allows you to run `python database.py` to create tables
    # Make sure your DATABASE_URL is set in a .env file or environment.
    create_db_and_tables()
    print(f"Connected to database: {DATABASE_URL.split('@')[-1]}")
```

File Name: models.py
```python
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from .database import Base # Import Base from our database connection

class User(Base):
    __tablename__ = "users"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to Bookings
    bookings = relationship("Booking", back_populates="user")

class Driver(Base):
    __tablename__ = "drivers"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    wallet_balance = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)

    # Relationship to Bookings
    bookings = relationship("Booking", back_populates="driver")

class Booking(Base):
    __tablename__ = "bookings"
    booking_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    driver_id = Column(PG_UUID(as_uuid=True), ForeignKey("drivers.id"), nullable=True) # Nullable until matched
    total_fare = Column(Float, nullable=False)
    status = Column(String, default="PENDING", index=True) # e.g., 'PENDING', 'CONFIRMED', 'COMPLETED', 'CANCELLED'
    pickup_address = Column(String, nullable=False)
    drop_address = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships to User and Driver
    user = relationship("User", back_populates="bookings")
    driver = relationship("Driver", back_populates="bookings")
```

File Name: schemas.py
```python
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
```

File Name: pricing.py
```python
# pricing.py - Module for calculating booking fare

FARE_PER_KM = 1.5
BASE_FARE = 5.0

def calculate_fare(distance_km: float) -> float:
    """
    Calculates the total fare based on the distance.
    A simple linear model: Base Fare + (Distance * Fare per KM).
    """
    if distance_km < 0:
        raise ValueError("Distance cannot be negative.")
    
    total_fare = BASE_FARE + (distance_km * FARE_PER_KM)
    return round(total_fare, 2) # Round to two decimal places
```

File Name: matching.py
```python
# matching.py - Module for driver matching and proximity calculations
from typing import List, Optional
from haversine import haversine, Unit
from sqlalchemy.orm import Session
from .models import Driver

def find_closest_driver(
    db: Session,
    pickup_latitude: float,
    pickup_longitude: float,
    min_wallet_balance: float = 20.0
) -> Optional[Driver]:
    """
    Finds the closest active driver with a sufficient wallet balance from the database.

    Args:
        db: SQLAlchemy session.
        pickup_latitude: Latitude of the pickup location.
        pickup_longitude: Longitude of the pickup location.
        min_wallet_balance: Minimum wallet balance required for a driver to be eligible.

    Returns:
        The closest Driver object, or None if no suitable driver is found.
    """
    # Query all active drivers with sufficient wallet balance
    eligible_drivers: List[Driver] = db.query(Driver).filter(
        Driver.is_active == True,
        Driver.wallet_balance >= min_wallet_balance
    ).all()

    if not eligible_drivers:
        return None

    pickup_coords = (pickup_latitude, pickup_longitude)
    closest_driver: Optional[Driver] = None
    min_distance_km = float('inf')

    for driver in eligible_drivers:
        driver_coords = (driver.latitude, driver.longitude)
        distance = haversine(pickup_coords, driver_coords, unit=Unit.KILOMETERS)

        if distance < min_distance_km:
            min_distance_km = distance
            closest_driver = driver
            
    return closest_driver

def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates the Haversine distance between two sets of coordinates in kilometers.
    """
    coords1 = (lat1, lon1)
    coords2 = (lat2, lon2)
    return haversine(coords1, coords2, unit=Unit.KILOMETERS)
```

File Name: app.py
```python
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid

# Local imports
from . import models, schemas, pricing, matching
from .database import engine, get_db, create_db_and_tables # Import create_db_and_tables

app = FastAPI(
    title="RideShare API (Database Edition)",
    description="A simple ride-sharing application with FastAPI, SQLAlchemy, and PostgreSQL.",
    version="1.0.0"
)

# --- Startup Event ---
@app.on_event("startup")
def on_startup():
    """
    Event handler for application startup.
    Ensures all database tables are created before the application starts serving requests.
    In a production environment, you would typically use a migration tool like Alembic.
    """
    create_db_and_tables()
    print("FastAPI application started and database tables ensured.")


# --- Health Check ---
@app.get("/", summary="Health Check", tags=["System"])
async def root():
    return {"message": "RideShare API is running!"}


# --- User Endpoints ---
@app.post("/users/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED, tags=["Users"])
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = models.User(name=user.name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/", response_model=List[schemas.UserResponse], tags=["Users"])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

@app.get("/users/{user_id}", response_model=schemas.UserResponse, tags=["Users"])
def read_user(user_id: uuid.UUID, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


# --- Driver Endpoints ---
@app.post("/drivers/", response_model=schemas.DriverResponse, status_code=status.HTTP_201_CREATED, tags=["Drivers"])
def create_driver(driver: schemas.DriverCreate, db: Session = Depends(get_db)):
    db_driver = models.Driver(**driver.model_dump())
    db.add(db_driver)
    db.commit()
    db.refresh(db_driver)
    return db_driver

@app.get("/drivers/", response_model=List[schemas.DriverResponse], tags=["Drivers"])
def read_drivers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    drivers = db.query(models.Driver).offset(skip).limit(limit).all()
    return drivers

@app.get("/drivers/{driver_id}", response_model=schemas.DriverResponse, tags=["Drivers"])
def read_driver(driver_id: uuid.UUID, db: Session = Depends(get_db)):
    driver = db.query(models.Driver).filter(models.Driver.id == driver_id).first()
    if driver is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
    return driver


# --- Booking Endpoints ---
@app.post("/book", response_model=schemas.BookingResponse, status_code=status.HTTP_201_CREATED, tags=["Bookings"])
def create_booking(booking_request: schemas.BookingRequest, db: Session = Depends(get_db)):
    # 1. Validate User
    user = db.query(models.User).filter(models.User.id == booking_request.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    # 2. Find Closest Eligible Driver
    pickup_coords = (booking_request.pickup_latitude, booking_request.pickup_longitude)
    drop_coords = (booking_request.drop_latitude, booking_request.drop_longitude)

    closest_driver = matching.find_closest_driver(
        db,
        pickup_coords[0],
        pickup_coords[1]
    )

    if not closest_driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active drivers found or available with sufficient wallet balance."
        )

    # 3. Calculate Distance and Fare
    trip_distance_km = matching.calculate_distance_km(
        pickup_coords[0], pickup_coords[1],
        drop_coords[0], drop_coords[1]
    )
    total_fare = pricing.calculate_fare(trip_distance_km)

    # 4. Create and Save Booking to Database
    new_booking = models.Booking(
        user_id=booking_request.user_id,
        driver_id=closest_driver.id,  # Assign the matched driver
        total_fare=total_fare,
        status="CONFIRMED", # Or PENDING, depending on business logic
        pickup_address=booking_request.pickup_address,
        drop_address=booking_request.drop_address,
        created_at=models.datetime.utcnow() # Use models.datetime to prevent conflict with global datetime
    )

    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

    return new_booking

@app.get("/bookings/{booking_id}", response_model=schemas.BookingResponse, tags=["Bookings"])
def get_booking_details(booking_id: uuid.UUID, db: Session = Depends(get_db)):
    booking = db.query(models.Booking).filter(models.Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found.")
    return booking

@app.get("/bookings/", response_model=List[schemas.BookingResponse], tags=["Bookings"])
def list_bookings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    bookings = db.query(models.Booking).offset(skip).limit(limit).all()
    return bookings

# Optional: Seed initial data for testing
@app.post("/seed_data", status_code=status.HTTP_200_OK, tags=["System"])
def seed_data(db: Session = Depends(get_db)):
    # Check if data already exists to avoid duplicates on multiple runs
    if db.query(models.User).count() > 0 or db.query(models.Driver).count() > 0:
        return {"message": "Data already exists. Skipping seeding."}

    user1 = models.User(name="Alice Wonderland")
    user2 = models.User(name="Charlie Chaplin")

    driver1 = models.Driver(name="David Driver", latitude=34.053, longitude=-118.245, wallet_balance=150.0, is_active=True)
    driver2 = models.Driver(name="Eve Escort", latitude=34.055, longitude=-118.250, wallet_balance=10.0, is_active=True) # Low balance
    driver3 = models.Driver(name="Frank Fast", latitude=34.060, longitude=-118.240, wallet_balance=200.0, is_active=False) # Inactive
    driver4 = models.Driver(name="Grace Go", latitude=34.050, longitude=-118.240, wallet_balance=75.0, is_active=True) # Closer to example pickup

    db.add_all([user1, user2, driver1, driver2, driver3, driver4])
    db.commit()
    return {"message": "Sample users and drivers seeded successfully!"}

```