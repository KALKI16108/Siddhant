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