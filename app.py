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