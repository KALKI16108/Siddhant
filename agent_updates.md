File Name: schemas.py
```python
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
```

File Name: database.py
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLite database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"

# Create a SQLAlchemy engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create a SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class for declarative models
Base = declarative_base()

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

File Name: models.py
```python
from sqlalchemy import Column, Integer, String
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
```

File Name: crud.py
```python
from sqlalchemy.orm import Session
from models import User
from schemas import UserCreate

def get_user(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def create_user(db: Session, user: UserCreate, hashed_password: str):
    db_user = User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
```

File Name: auth.py
```python
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from schemas import TokenData
from crud import get_user
from database import get_db

# Configuration for JWT
SECRET_KEY = "your-super-secret-key" # In a real app, use environment variables
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2PasswordBearer for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user
```

File Name: pricing.py
```python
from schemas import DeliveryRequest, DeliveryPrice
import random
import math

def calculate_price(request: DeliveryRequest) -> DeliveryPrice:
    """
    Calculates the estimated price for a delivery request.
    This is a placeholder function with basic logic.
    In a real system, this would involve complex factors like:
    - Distance between origin and destination (using geo-encoding)
    - Weight and dimensions (for vehicle type, fuel, handling)
    - Urgency/delivery speed
    - Current traffic conditions
    - Dynamic pricing based on demand/supply
    - Specific routes/tolls
    """
    # Simulate distance calculation (very basic, based on string length difference)
    # A real system would use a mapping API (e.g., Google Maps, OpenStreetMap)
    distance_factor = abs(len(request.origin) - len(request.destination)) / 10 + 1
    
    # Weight and dimension factors
    weight_factor = max(1.0, request.weight_kg / 10.0) # Base price increases with weight
    
    # Simple volume calculation
    volume_cm3 = math.prod(request.dimensions_cm)
    volume_factor = max(1.0, volume_cm3 / 10000.0) # Base price increases with volume (10,000 cm3 = 10L)

    # Base price
    base_price = 5.0

    # Combine factors (this is purely illustrative)
    total_amount = base_price * distance_factor * weight_factor * volume_factor
    
    # Add a random fluctuation for realism
    total_amount *= random.uniform(0.9, 1.1)

    # Estimate duration based on distance factor (very rough)
    estimated_duration_minutes = int(30 * distance_factor + request.weight_kg * 2 + random.randint(5, 15))
    
    return DeliveryPrice(
        amount=round(total_amount, 2),
        currency="USD",
        estimated_duration_minutes=max(15, estimated_duration_minutes) # Minimum 15 minutes
    )
```

File Name: matching.py
```python
from schemas import DeliveryRequest, DeliveryMatch
import random

def find_match(request: DeliveryRequest) -> DeliveryMatch:
    """
    Finds a suitable driver/delivery partner for a given delivery request.
    This is a placeholder function with basic logic.
    In a real system, this would involve complex algorithms like:
    - Geospatial indexing of available drivers
    - Driver availability and current workload
    - Driver vehicle capabilities (size, weight limits)
    - Driver ratings and preferences
    - Optimization for route efficiency and minimizing pickup/delivery times
    - Real-time traffic data
    """
    
    # Simulate finding an available driver
    # In reality, this would query a database of active drivers
    mock_drivers = [
        {"id": "DRV001", "name": "Alice Smith", "phone": "+15551234567"},
        {"id": "DRV002", "name": "Bob Johnson", "phone": "+15559876543"},
        {"id": "DRV003", "name": "Charlie Brown", "phone": "+15551112233"},
    ]
    
    selected_driver = random.choice(mock_drivers)

    # Simulate estimated times based on request complexity
    # More complex logic would use geographical distance and traffic
    estimated_pickup = random.randint(5, 20) # minutes
    estimated_delivery = random.randint(estimated_pickup + 30, estimated_pickup + 90) # minutes

    return DeliveryMatch(
        driver_id=selected_driver["id"],
        estimated_pickup_time_minutes=estimated_pickup,
        estimated_delivery_time_minutes=estimated_delivery,
        driver_name=selected_driver["name"],
        driver_phone=selected_driver["phone"]
    )
```

File Name: app.py
```python
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
```

File Name: test_app.py
```python
from fastapi.testclient import TestClient
from fastapi import status
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import sys
import os

# Add the current directory to the path to ensure imports work correctly
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app
from database import Base, get_db
from models import User

# Use a separate test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# Create a test engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool, # Use StaticPool for SQLite in-memory for testing
)

# Create a TestSessionLocal
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db dependency
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# --- Helper functions for setup and teardown ---
def setup_test_db():
    Base.metadata.create_all(bind=engine)

def teardown_test_db():
    Base.metadata.drop_all(bind=engine)

# --- Test Cases ---

def test_root():
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Welcome to the Delivery Service API! Please register or login."}

def test_register_user():
    teardown_test_db() # Ensure clean state
    setup_test_db()

    response = client.post(
        "/register",
        json={"username": "testuser", "password": "testpassword"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["username"] == "testuser"

    # Try to register same user again
    response = client.post(
        "/register",
        json={"username": "testuser", "password": "anotherpassword"}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Username already registered"

def test_login_for_access_token():
    teardown_test_db() # Ensure clean state
    setup_test_db()

    # Register a user first
    client.post(
        "/register",
        json={"username": "testuser_login", "password": "testpassword_login"}
    )

    # Login with correct credentials
    response = client.post(
        "/token",
        data={"username": "testuser_login", "password": "testpassword_login"}
    )
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

    # Login with incorrect password
    response = client.post(
        "/token",
        data={"username": "testuser_login", "password": "wrong_password"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Incorrect username or password"

    # Login with non-existent user
    response = client.post(
        "/token",
        data={"username": "nonexistent_user", "password": "any_password"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_read_users_me_protected():
    teardown_test_db()
    setup_test_db()

    # Register and login
    client.post(
        "/register",
        json={"username": "secure_user", "password": "secure_password"}
    )
    token_response = client.post(
        "/token",
        data={"username": "secure_user", "password": "secure_password"}
    )
    access_token = token_response.json()["access_token"]

    # Access protected endpoint with token
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == "secure_user"

    # Access protected endpoint without token
    response = client.get("/users/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Access protected endpoint with invalid token
    response = client.get(
        "/users/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_delivery_endpoints_protected():
    teardown_test_db()
    setup_test_db()

    # Register and login
    client.post(
        "/register",
        json={"username": "delivery_user", "password": "delivery_password"}
    )
    token_response = client.post(
        "/token",
        data={"username": "delivery_user", "password": "delivery_password"}
    )
    access_token = token_response.json()["access_token"]

    delivery_request_payload = {
        "origin": "100 Test St",
        "destination": "200 Test Ave",
        "weight_kg": 10.0,
        "dimensions_cm": [30.0, 20.0, 10.0]
    }

    # --- Test /delivery/estimate_price ---
    # Without authentication
    response = client.post("/delivery/estimate_price", json=delivery_request_payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # With authentication
    response = client.post(
        "/delivery/estimate_price",
        json=delivery_request_payload,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    assert "amount" in response.json()
    assert "currency" in response.json()
    assert "estimated_duration_minutes" in response.json()
    assert response.json()["amount"] > 0
    assert response.json()["estimated_duration_minutes"] > 0

    # --- Test /delivery/find_match ---
    # Without authentication
    response = client.post("/delivery/find_match", json=delivery_request_payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # With authentication
    response = client.post(
        "/delivery/find_match",
        json=delivery_request_payload,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    assert "driver_id" in response.json()
    assert "estimated_pickup_time_minutes" in response.json()
    assert "estimated_delivery_time_minutes" in response.json()
    assert "driver_name" in response.json()
    assert "driver_phone" in response.json()
    assert response.json()["estimated_pickup_time_minutes"] > 0
    assert response.json()["estimated_delivery_time_minutes"] > 0

    # --- Test /delivery/book ---
    # Without authentication
    response = client.post("/delivery/book", json=delivery_request_payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # With authentication
    response = client.post(
        "/delivery/book",
        json=delivery_request_payload,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert "delivery_id" in response.json()
    assert "status" in response.json()
    assert response.json()["status"] == "booked"
    assert "message" in response.json()
    assert "delivery_user" in response.json()["message"] # Ensure it mentions the user
    assert "driver" in response.json()["message"] # Ensure it mentions a driver
    assert "price" in response.json()["message"] # Ensure it mentions the price
```