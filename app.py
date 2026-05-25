from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
import random
import string

from schemas import UserCreate, Token, UserBase, DeliveryRequest, DeliveryConfirmation, DeliveryPrice, DeliveryMatch
from database import SessionLocal, engine, Base, get_db
from models import User
from crud import create_user, get_user
from auth import (
    verify_password, get_password_hash,
    create_access_token, get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
import pricing
import matching

app = FastAPI(
    title="Delivery Service API with User Authentication",
    description="API for managing user authentication and booking deliveries, secured with JWT."
)

# Initialize database tables on startup
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

# Dependency to get the database session
# This is already defined in database.py, but good to ensure it's imported here if not used directly
# from database import get_db

@app.get("/", tags=["Root"])
async def root():
    return {"message": "Welcome to the Delivery Service API! Please register or login."}

# --- User Authentication Endpoints ---

@app.post("/register", response_model=UserBase, status_code=status.HTTP_201_CREATED, tags=["Authentication"])
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
    
    hashed_password = get_password_hash(user.password)
    db_user = create_user(db=db, user=user, hashed_password=hashed_password)
    return db_user

@app.post("/token", response_model=Token, tags=["Authentication"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user(db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=UserBase, tags=["Users"])
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# --- Delivery Service Endpoints (Protected) ---

@app.post("/delivery/estimate_price", response_model=DeliveryPrice, tags=["Delivery"], 
          summary="Get an estimated price for a delivery request",
          description="Calculates a hypothetical price for a delivery based on origin, destination, weight, and dimensions. Requires authentication.")
async def estimate_delivery_price(
    request: DeliveryRequest,
    current_user: User = Depends(get_current_user) # Protect this endpoint
):
    """
    Calculates the estimated price for a delivery request.
    """
    price_estimate = pricing.calculate_price(request)
    return price_estimate

@app.post("/delivery/find_match", response_model=DeliveryMatch, tags=["Delivery"],
          summary="Finds a suitable driver match for a delivery request",
          description="Identifies a potential driver and provides estimated pickup/delivery times. Requires authentication.")
async def find_delivery_match(
    request: DeliveryRequest,
    current_user: User = Depends(get_current_user) # Protect this endpoint
):
    """
    Finds a suitable driver for the delivery request.
    """
    driver_match = matching.find_match(request)
    return driver_match


@app.post("/delivery/book", response_model=DeliveryConfirmation, status_code=status.HTTP_201_CREATED, tags=["Delivery"],
          summary="Book a delivery",
          description="Processes a delivery request, calculates price, finds a driver, and confirms the booking. Requires authentication.")
async def book_delivery(
    request: DeliveryRequest,
    current_user: User = Depends(get_current_user) # Protect this endpoint
):
    """
    Books a new delivery. This endpoint simulates the full booking process:
    1. Calculates the estimated price.
    2. Finds a suitable driver.
    3. Confirms the booking.
    """
    # Step 1: Calculate price
    price_estimate = pricing.calculate_price(request)
    # print(f"User {current_user.username} - Estimated price: {price_estimate.amount} {price_estimate.currency}")

    # Step 2: Find a driver match
    driver_match = matching.find_match(request)
    # print(f"User {current_user.username} - Driver matched: {driver_match.driver_name}")

    # Step 3: Simulate booking confirmation
    # In a real application, this would involve:
    # - Storing the delivery request and assigned driver in a database
    # - Notifying the driver
    # - Notifying the user
    # - Handling payment processing (if applicable)
    
    delivery_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

    return DeliveryConfirmation(
        delivery_id=f"DEL-{delivery_id}",
        status="booked",
        message=f"Delivery successfully booked for user {current_user.username} "
                f"with driver {driver_match.driver_name}. "
                f"Estimated price: {price_estimate.amount} {price_estimate.currency}."
    )