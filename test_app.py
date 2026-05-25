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