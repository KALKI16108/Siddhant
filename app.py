from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from sqlalchemy import Column, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base

import math
from typing import AsyncGenerator
from contextlib import asynccontextmanager

# Import schemas defined in schemas.py
from schemas import DriverLocationUpdate, DriverStatusUpdate, OrderTrackingResponse

# --- Database Configuration ---
# In a real application, these credentials would be loaded from environment variables
DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/your_database_name"

engine = create_async_engine(DATABASE_URL, echo=False) # echo=True for debugging SQL queries
AsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False, # Important for asynchronous sessions
)

Base = declarative_base()

# --- Database Models ---
# These models define the structure of your database tables
class Driver(Base):
    __tablename__ = "drivers"
    driver_id = Column(String, primary_key=True, index=True)
    latitude = Column(Float, nullable=False, default=0.0)
    longitude = Column(Float, nullable=False, default=0.0)
    is_active = Column(Boolean, nullable=False, default=True) # Driver's on/off duty status

class Booking(Base):
    __tablename__ = "bookings"
    booking_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    pickup_latitude = Column(Float, nullable=False)
    pickup_longitude = Column(Float, nullable=False)
    dropoff_latitude = Column(Float, nullable=False)
    dropoff_longitude = Column(Float, nullable=False)
    assigned_driver_id = Column(String, ForeignKey("drivers.driver_id"), nullable=True)
    status = Column(String, nullable=False, default="pending") # e.g., 'pending', 'accepted', 'en_route', 'completed', 'cancelled'

# --- Utility Functions ---
def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates the Haversine distance between two points on Earth
    given their latitudes and longitudes in degrees.
    Returns distance in kilometers.
    """
    R = 6371  # Earth radius in kilometers

    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance # in kilometers

# --- FastAPI App Lifecycle ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup, create database tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # No specific cleanup needed for the engine itself as it manages connection pools

app = FastAPI(
    title="Real-time Ride-Sharing Backend",
    description="API for managing driver telemetry, order tracking, and driver lifecycle statuses.",
    version="1.0.0",
    lifespan=lifespan
)

# --- Database Dependency ---
# This function yields an asynchronous database session for each request
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

# --- API Endpoints ---

@app.post("/driver/update-location", status_code=status.HTTP_200_OK)
async def update_driver_location(
    location_update: DriverLocationUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    **Driver Telemetry Ping**
    Accepts driver coordinates and updates their real-time position in the database.
    If the driver_id does not exist, a new driver record is created automatically.
    """
    # Try to find the driver by ID
    result = await db.execute(
        select(Driver).where(Driver.driver_id == location_update.driver_id)
    )
    driver = result.scalars().first()

    if driver:
        # Update existing driver's coordinates
        driver.latitude = location_update.latitude
        driver.longitude = location_update.longitude
    else:
        # If driver doesn't exist, create a new record
        new_driver = Driver(
            driver_id=location_update.driver_id,
            latitude=location_update.latitude,
            longitude=location_update.longitude,
            is_active=True # New drivers are active by default
        )
        db.add(new_driver)
    
    await db.commit() # Commit changes to the database
    return {"message": f"Driver {location_update.driver_id} location updated successfully."}

@app.get("/booking/{booking_id}/track", response_model=OrderTrackingResponse)
async def track_order(
    booking_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    **Order Tracking Route**
    Fetches an active booking record, joins with the assigned driver's location,
    and calculates the estimated time of arrival (ETA) for the driver to reach
    the pickup location.
    """
    # Fetch booking and potentially its assigned driver in a single query
    result = await db.execute(
        select(Booking, Driver)
        .outerjoin(Driver, Booking.assigned_driver_id == Driver.driver_id)
        .where(Booking.booking_id == booking_id)
    )
    booking_driver_row = result.first()

    if not booking_driver_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found.")
    
    booking, driver = booking_driver_row # Unpack the row

    eta_minutes = None
    # Calculate ETA only if a driver is assigned and has valid coordinates, and booking has pickup
    if driver and driver.latitude is not None and driver.longitude is not None \
       and booking.pickup_latitude is not None and booking.pickup_longitude is not None:
        
        # Calculate Haversine distance from driver's current location to the booking's pickup location
        distance_to_pickup_km = haversine_distance(
            driver.latitude, driver.longitude,
            booking.pickup_latitude, booking.pickup_longitude
        )
        
        # Assume an average city transit speed of 20 km/h
        AVERAGE_CITY_SPEED_KM_PER_HOUR = 20
        if AVERAGE_CITY_SPEED_KM_PER_HOUR > 0:
            eta_hours = distance_to_pickup_km / AVERAGE_CITY_SPEED_KM_PER_HOUR
            eta_minutes = round(eta_hours * 60, 2) # Convert to minutes and round

    return OrderTrackingResponse(
        booking_id=booking.booking_id,
        user_id=booking.user_id,
        status=booking.status,
        pickup_latitude=booking.pickup_latitude,
        pickup_longitude=booking.pickup_longitude,
        dropoff_latitude=booking.dropoff_latitude,
        dropoff_longitude=booking.dropoff_longitude,
        driver_id=driver.driver_id if driver else None,
        driver_latitude=driver.latitude if driver else None,
        driver_longitude=driver.longitude if driver else None,
        eta_minutes=eta_minutes
    )

@app.post("/driver/status", status_code=status.HTTP_200_OK)
async def update_driver_status(
    status_update: DriverStatusUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    **Driver Lifecycle Toggles**
    Allows a driver to toggle their 'is_active' status (On Duty / Off Duty),
    instantly updating their availability for dispatch rounds.
    """
    # Find the driver by ID
    result = await db.execute(
        select(Driver).where(Driver.driver_id == status_update.driver_id)
    )
    driver = result.scalars().first()

    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found.")
    
    # Update the driver's active status
    driver.is_active = status_update.is_active
    await db.commit() # Commit changes to the database
    
    status_text = "active (On Duty)" if status_update.is_active else "inactive (Off Duty)"
    return {"message": f"Driver {status_update.driver_id} status updated to {status_text}."}

# Example of a root endpoint (can be expanded)
@app.get("/")
async def root():
    return {"message": "Welcome to the Ride-Sharing Backend API!"}