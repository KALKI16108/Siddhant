File Name: index.html
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dispatch Dashboard</title>
    <!-- Leaflet CSS -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
     integrity="sha256-p4NxAoJBhIIN+hmNHrzJjQFX+vGeFVieYN8GpPyWTNA="
     crossorigin=""/>
    <style>
        /* Basic Reset & Typography */
        *, *::before, *::after {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f4f7f6;
            height: 100vh;
            display: flex;
            overflow: hidden; /* Prevent body scroll, layout handles content */
        }

        /* Dashboard Layout (Flexbox) */
        .dashboard-container {
            display: flex;
            width: 100%;
            height: 100%;
        }

        .sidebar {
            flex: 0 0 35%; /* 35% width, non-growable, non-shrinkable */
            background-color: #ffffff;
            padding: 2rem;
            box-shadow: 2px 0 10px rgba(0,0,0,0.05);
            display: flex;
            flex-direction: column;
            overflow-y: auto; /* Scroll for sidebar content if it overflows */
        }

        .map-viewport {
            flex: 1; /* Takes remaining 65% width */
            position: relative;
            background-color: #e0e0e0; /* Placeholder */
        }

        #map {
            width: 100%;
            height: 100%;
            border-radius: 8px; /* Slightly rounded corners for map */
        }

        /* Sidebar Content Styling */
        h1 {
            color: #2c3e50;
            margin-bottom: 1.5rem;
            font-size: 1.8rem;
            font-weight: 600;
            border-bottom: 1px solid #eee;
            padding-bottom: 1rem;
        }

        .form-section {
            margin-bottom: 2rem;
            padding-bottom: 1.5rem;
            border-bottom: 1px solid #f0f0f0;
        }

        .form-group {
            margin-bottom: 1rem;
        }

        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
            color: #555;
            font-size: 0.9rem;
        }

        .form-group input[type="text"],
        .form-group input[type="hidden"] {
            width: 100%;
            padding: 0.8rem;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 0.95rem;
            transition: border-color 0.2s ease-in-out;
            background-color: #fcfcfc;
        }
        .form-group input[type="text"]:focus {
            outline: none;
            border-color: #007bff;
            box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
        }

        #dispatchButton {
            width: 100%;
            padding: 1rem 1.5rem;
            background-color: #007bff; /* Bright blue */
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: background-color 0.2s ease-in-out, transform 0.1s ease;
            margin-top: 1.5rem;
            box-shadow: 0 4px 10px rgba(0, 123, 255, 0.3);
        }

        #dispatchButton:hover {
            background-color: #0056b3;
            transform: translateY(-2px);
        }

        #dispatchButton:active {
            transform: translateY(0);
            box-shadow: 0 2px 5px rgba(0, 123, 255, 0.3);
        }

        /* Tracking Console Card */
        .tracking-card {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 1.5rem;
            margin-top: 1rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }

        .tracking-card h3 {
            color: #34495e;
            font-size: 1.3rem;
            margin-bottom: 1rem;
            border-bottom: 1px solid #e9ecef;
            padding-bottom: 0.8rem;
        }

        .tracking-card p {
            margin-bottom: 0.7rem;
            font-size: 1rem;
            color: #495057;
        }

        .tracking-card p strong {
            color: #212529;
            font-weight: 600;
        }

        #statusBadge {
            margin-top: 1rem;
            padding: 0.6rem 1rem;
            background-color: #d1ecf1; /* Light blue background */
            color: #0c5460; /* Darker blue text */
            border: 1px solid #bee5eb;
            border-radius: 20px;
            text-align: center;
            font-weight: 600;
            font-size: 0.9rem;
            display: inline-block;
            opacity: 0; /* Hidden initially */
            transform: scale(0.8); /* Smaller initially */
            transition: opacity 0.5s ease-out, transform 0.5s ease-out;
        }

        /* Animation for status badge */
        #statusBadge.animate {
            animation: pulse-and-fade 2s infinite ease-out;
            opacity: 1;
            transform: scale(1);
        }

        @keyframes pulse-and-fade {
            0% {
                transform: scale(0.95);
                opacity: 0.7;
            }
            50% {
                transform: scale(1.05);
                opacity: 1;
            }
            100% {
                transform: scale(0.95);
                opacity: 0.7;
            }
        }

        #statusBadge.confirmed {
            background-color: #d4edda; /* Greenish for confirmed */
            color: #155724;
            border-color: #c3e6cb;
        }

        /* Leaflet custom marker icons (optional but good for visual distinction) */
        .leaflet-marker-icon.pickup-marker {
            /* Example: Custom styling for green marker */
            filter: hue-rotate(100deg) brightness(0.9);
        }
        .leaflet-marker-icon.dropoff-marker {
            /* Example: Custom styling for red marker */
            filter: hue-rotate(0deg) brightness(0.9);
        }
    </style>
</head>
<body>
    <div class="dashboard-container">
        <aside class="sidebar">
            <h1>Dispatch Dashboard</h1>

            <section class="form-section">
                <div class="form-group">
                    <label for="userId">User ID:</label>
                    <input type="text" id="userId" placeholder="Enter User ID (e.g., U123)" value="U123">
                </div>

                <div class="form-group">
                    <label for="pickupAddress">Pickup Address:</label>
                    <input type="text" id="pickupAddress" placeholder="Double-click map for pickup point" readonly>
                    <input type="hidden" id="pickupLat">
                    <input type="hidden" id="pickupLng">
                </div>

                <div class="form-group">
                    <label for="dropoffAddress">Drop-off Address:</label>
                    <input type="text" id="dropoffAddress" placeholder="Double-click map for drop-off point" readonly>
                    <input type="hidden" id="dropoffLat">
                    <input type="hidden" id="dropoffLng">
                </div>

                <button id="dispatchButton">Calculate & Dispatch</button>
            </section>

            <section class="tracking-card">
                <h3>Real-time Tracking Console</h3>
                <p>Total Fare: <strong id="fareDisplay">N/A</strong></p>
                <p>Assigned Driver: <strong id="driverDisplay">N/A</strong></p>
                <div id="statusBadge"></div>
            </section>
        </aside>

        <main class="map-viewport">
            <div id="map"></div>
        </main>
    </div>

    <!-- Leaflet JS -->
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
     integrity="sha256-p4NxAoJBhIIN+hmNHrzJjQFX+vGeFVieYN8GpPyWTNA="
     crossorigin=""></script>
    <script>
        // Initialize the map
        const map = L.map('map').setView([19.0760, 72.8777], 13); // Centered over Mumbai

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        }).addTo(map);

        // Custom Marker Icons
        const greenIcon = new L.Icon({
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
            shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowSize: [41, 41]
        });

        const redIcon = new L.Icon({
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
            shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowSize: [41, 41]
        });

        // Global variables for markers and coordinates
        let pickupMarker = null;
        let dropoffMarker = null;
        let mapClickCounter = 0; // To track first or second double-click

        // DOM Elements
        const userIdInput = document.getElementById('userId');
        const pickupAddressInput = document.getElementById('pickupAddress');
        const pickupLatInput = document.getElementById('pickupLat');
        const pickupLngInput = document.getElementById('pickupLng');
        const dropoffAddressInput = document.getElementById('dropoffAddress');
        const dropoffLatInput = document.getElementById('dropoffLat');
        const dropoffLngInput = document.getElementById('dropoffLng');
        const dispatchButton = document.getElementById('dispatchButton');
        const fareDisplay = document.getElementById('fareDisplay');
        const driverDisplay = document.getElementById('driverDisplay');
        const statusBadge = document.getElementById('statusBadge');

        // Function to update address inputs with coordinates (mock reverse geocoding)
        function updateAddressInputs(latlng, type) {
            const addressText = `Lat: ${latlng.lat.toFixed(4)}, Lng: ${latlng.lng.toFixed(4)}`;
            if (type === 'pickup') {
                pickupAddressInput.value = addressText;
                pickupLatInput.value = latlng.lat;
                pickupLngInput.value = latlng.lng;
            } else {
                dropoffAddressInput.value = addressText;
                dropoffLatInput.value = latlng.lat;
                dropoffLngInput.value = latlng.lng;
            }
        }

        // Map Double-Click Listener
        map.on('dblclick', function(e) {
            mapClickCounter++;

            if (mapClickCounter % 2 !== 0) { // First double-click: Pickup
                if (pickupMarker) {
                    map.removeLayer(pickupMarker);
                }
                pickupMarker = L.marker(e.latlng, { icon: greenIcon }).addTo(map)
                    .bindPopup('<b>Pickup Point</b>').openPopup();
                updateAddressInputs(e.latlng, 'pickup');
            } else { // Second double-click: Drop-off
                if (dropoffMarker) {
                    map.removeLayer(dropoffMarker);
                }
                dropoffMarker = L.marker(e.latlng, { icon: redIcon }).addTo(map)
                    .bindPopup('<b>Drop-off Point</b>').openPopup();
                updateAddressInputs(e.latlng, 'dropoff');
            }

            // After placing two markers, potentially reset counter or prepare for next pair
            // Or just let it cycle, placing a new pickup after a dropoff if user keeps clicking.
            // For clarity, we can reset if both are set and user clicks again, for a new journey.
            if (pickupMarker && dropoffMarker && mapClickCounter % 2 === 0) {
                 // Optionally, reset mapClickCounter to allow new pickup to be first dbl-click after this.
                 // mapClickCounter = 0; // This would clear existing markers on next dbl-click.
                 // For now, it cycles. 1st click = pickup, 2nd = dropoff, 3rd = new pickup, 4th = new dropoff.
            }
        });

        // "Calculate & Dispatch" Button Listener
        dispatchButton.addEventListener('click', async () => {
            const userId = userIdInput.value.trim();
            const pickupLat = parseFloat(pickupLatInput.value);
            const pickupLng = parseFloat(pickupLngInput.value);
            const dropoffLat = parseFloat(dropoffLatInput.value);
            const dropoffLng = parseFloat(dropoffLngInput.value);

            if (!userId) {
                alert('Please enter a User ID.');
                return;
            }
            if (isNaN(pickupLat) || isNaN(pickupLng)) {
                alert('Please double-click on the map to set a Pickup Point.');
                return;
            }
            if (isNaN(dropoffLat) || isNaN(dropoffLng)) {
                alert('Please double-click on the map to set a Drop-off Point.');
                return;
            }

            dispatchButton.disabled = true;
            dispatchButton.textContent = 'Dispatching...';
            statusBadge.classList.remove('animate', 'confirmed');
            statusBadge.style.opacity = '0'; // Hide initially

            try {
                const response = await fetch('http://127.0.0.1:5000/book', { // Assuming backend runs on port 5000
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        user_id: userId,
                        pickup_point: { latitude: pickupLat, longitude: pickupLng },
                        dropoff_point: { latitude: dropoffLat, longitude: dropoffLng }
                    }),
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
                }

                const data = await response.json();
                
                fareDisplay.textContent = `₹ ${data.total_fare.toFixed(2)}`;
                driverDisplay.textContent = data.driver_name;
                
                statusBadge.textContent = `🚚 ${data.status}`;
                statusBadge.classList.add('animate', 'confirmed'); // Add animation and confirmed style
                statusBadge.style.opacity = '1';

            } catch (error) {
                console.error('Error during dispatch:', error);
                fareDisplay.textContent = 'Error';
                driverDisplay.textContent = 'Error';
                statusBadge.textContent = `❌ Dispatch Failed: ${error.message}`;
                statusBadge.classList.remove('animate', 'confirmed');
                statusBadge.style.opacity = '1';
                statusBadge.style.backgroundColor = '#f8d7da';
                statusBadge.style.borderColor = '#f5c6cb';
                statusBadge.style.color = '#721c24';

            } finally {
                dispatchButton.disabled = false;
                dispatchButton.textContent = 'Calculate & Dispatch';
            }
        });
    </script>
</body>
</html>
```
File Name: schemas.py
```python
from pydantic import BaseModel
from typing import Tuple, List

class Coordinates(BaseModel):
    """Represents geographical coordinates."""
    latitude: float
    longitude: float

class BookingRequest(BaseModel):
    """Schema for the incoming booking request."""
    user_id: str
    pickup_point: Coordinates
    dropoff_point: Coordinates

class BookingResponse(BaseModel):
    """Schema for the outgoing booking response."""
    total_fare: float
    driver_name: str
    status: str
    # You could add more fields here like:
    # estimated_eta: int # in minutes
    # driver_location: Coordinates
    # route_points: List[Coordinates]
```
File Name: pricing.py
```python
import math
from typing import Tuple

def calculate_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """
    Calculates the great-circle distance between two points on the Earth
    (specified in decimal degrees) using the Haversine formula.

    Args:
        p1 (Tuple[float, float]): (latitude, longitude) of the first point.
        p2 (Tuple[float, float]): (latitude, longitude) of the second point.

    Returns:
        float: Distance in kilometers.
    """
    R = 6371  # Earth radius in kilometers

    lat1, lon1 = math.radians(p1[0]), math.radians(p1[1])
    lat2, lon2 = math.radians(p2[0]), math.radians(p2[1])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance

def calculate_fare(pickup_coords: Tuple[float, float], dropoff_coords: Tuple[float, float]) -> float:
    """
    Calculates a mock fare based on distance between pickup and dropoff points.

    Args:
        pickup_coords (Tuple[float, float]): (latitude, longitude) of pickup.
        dropoff_coords (Tuple[float, float]): (latitude, longitude) of dropoff.

    Returns:
        float: Rounded total fare.
    """
    distance_km = calculate_distance(pickup_coords, dropoff_coords)

    # Simple pricing model
    base_fare = 50.0  # INR
    per_km_rate = 15.0 # INR/km
    minimum_fare_distance_km = 1.0 # Minimum distance for full per_km_rate

    effective_distance_km = max(distance_km, minimum_fare_distance_km)
    fare = base_fare + (effective_distance_km * per_km_rate)

    # Add a surge factor for demonstration (e.g., random 1.0 to 1.5x)
    # surge_factor = 1.0 + (random.random() * 0.5)
    # fare *= surge_factor

    return round(fare, 2)
```
File Name: matching.py
```python
import random
from typing import Tuple, List

# A mock list of available drivers
AVAILABLE_DRIVERS: List[str] = ["Rajesh Kumar", "Priya Sharma", "Amit Singh", "Sunita Devi", "Vikram Patel", "Seema Rao"]

def assign_driver(pickup_coords: Tuple[float, float]) -> str:
    """
    Mocks the logic for assigning a driver.

    In a real-world system, this would involve:
    1. Querying a database or real-time service for nearby available drivers.
    2. Considering factors like driver's current location, estimated time of arrival (ETA),
       driver rating, vehicle type, and current demand.
    3. Potentially using optimization algorithms to find the best match.

    For this demonstration, it simply picks a random driver from a predefined list.

    Args:
        pickup_coords (Tuple[float, float]): The coordinates of the pickup point.
                                             (Not used in this mock but would be in real logic).

    Returns:
        str: The name of the assigned driver.
    """
    return random.choice(AVAILABLE_DRIVERS)
```
File Name: app.py
```python
from flask import Flask, request, jsonify
from flask_cors import CORS # Used for local development to allow frontend requests
import time # To simulate network delay

# Import backend logic modules
from schemas import BookingRequest, BookingResponse, Coordinates
from pricing import calculate_fare
from matching import assign_driver

app = Flask(__name__)
# Enable CORS for all routes, allowing requests from any origin during development.
# In a production environment, you would restrict this to specific origins.
CORS(app) 

@app.route('/book', methods=['POST'])
def book_ride():
    """
    Handles the ride booking request from the frontend.
    Validates input, calculates fare, assigns a driver, and returns booking details.
    """
    try:
        # Get JSON data from the request body
        data = request.get_json()
        if not data:
            raise ValueError("No JSON data provided.")

        # Validate request data using Pydantic schema
        booking_request = BookingRequest(**data)

        # Simulate network delay and backend processing time
        time.sleep(1.5) # A 1.5-second delay

        # Extract coordinates as tuples for calculations
        pickup_coords_tuple = (booking_request.pickup_point.latitude, booking_request.pickup_point.longitude)
        dropoff_coords_tuple = (booking_request.dropoff_point.latitude, booking_request.dropoff_point.longitude)

        # Apply backend logic
        total_fare = calculate_fare(pickup_coords_tuple, dropoff_coords_tuple)
        assigned_driver = assign_driver(pickup_coords_tuple)

        # Construct the response using Pydantic schema
        response = BookingResponse(
            total_fare=total_fare,
            driver_name=assigned_driver,
            status="DISPATCHED / CONFIRMED"
        )
        
        # Return the response as JSON
        return jsonify(response.dict()), 200

    except ValueError as ve:
        # Handle validation errors
        return jsonify({"error": f"Invalid input: {str(ve)}"}), 400
    except Exception as e:
        # Catch any other unexpected errors
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500

if __name__ == '__main__':
    # Run the Flask application
    # debug=True enables reloader and debugger (good for development)
    # host='0.0.0.0' makes the server accessible from other devices on the network
    # port=5000 is the default port the frontend expects
    app.run(debug=True, host='127.0.0.1', port=5000)
```