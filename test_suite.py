import pytest
from fastapi.testclient import TestClient
from app import app # Assuming app.py is in the same directory

# Initialize the TestClient with your FastAPI app
client = TestClient(app)

def test_api_health():
    """
    Test the root endpoint for a basic health check.
    Ensures the service is live and responsive.
    """
    response = client.get("/")
    assert response.status_code == 200
    # Asserting the exact status string returned by the app
    assert response.json()["status"] == "Sync engine live"

def test_pricing_and_booking_loop():
    """
    Tests the end-to-end booking flow:
    1. Sends a booking request.
    2. Verifies a successful response status code (200).
    3. Checks for essential fields in the response (booking_id, price, driver_id, status).
    4. Asserts the booking status is as expected ("CONFIRMED" based on our app's logic).
    5. Ensures numerical values (like price) are present and positive.
    """
    # Simulate a standard Mumbai booking payload
    payload = {
        "user_id": "Siddhant1709",
        "pickup_address": {
            "street": "Bandra West", "city": "Mumbai", "state": "MH", "postal_code": "400050",
            "location": {"latitude": 19.0500, "longitude": 72.8200}
        },
        "drop_address": {
            "street": "BKC Choke Point", "city": "Mumbai", "state": "MH", "postal_code": "400051",
            "location": {"latitude": 19.0600, "longitude": 72.8600}
        }
    }
    response = client.post("/book", json=payload)

    # Expecting a successful response for a valid booking request
    assert response.status_code == 200
    
    data = response.json()

    # Assert that critical fields are present and of the correct type
    assert "booking_id" in data
    assert isinstance(data["booking_id"], str)
    assert data["user_id"] == payload["user_id"] # User ID should be reflected back

    assert "price_usd" in data
    assert isinstance(data["price_usd"], (float, int))
    assert data["price_usd"] > 0 # Price should always be positive for a valid booking

    assert "driver_id" in data
    assert isinstance(data["driver_id"], str)
    # Our dummy matching always returns a driver, so we expect one here

    assert "status" in data
    # Based on our `app.py` logic, a successful booking will have a "CONFIRMED" status
    assert data["status"] == "CONFIRMED"

    # Further assertions on the structure of address objects, if desired, but
    # pydantic validation handles much of this at the API boundary.
    assert data["pickup_address"]["city"] == "Mumbai"
    assert data["drop_address"]["location"]["latitude"] == 19.0600