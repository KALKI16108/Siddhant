Here are the requested code files, each within a separate Python block and with the specified header format.

File Name: schemas.py
```python
"""
SQL schema structures for a Supabase PostgreSQL database.
These SQL commands can be executed directly in your Supabase SQL editor
or via a migration tool to set up the database tables.

To enable UUID generation (gen_random_uuid()), ensure you have the 'pgcrypto' extension enabled in Supabase:
CREATE EXTENSION IF NOT EXISTS pgcrypto;
"""

# Table for users
SQL_CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(), -- Using UUID for user IDs
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
"""

# Enum for driver status
SQL_CREATE_DRIVER_STATUS_ENUM = """
DO $$ BEGIN
    CREATE TYPE driver_status AS ENUM ('available', 'busy', 'offline');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;
"""

# Enum for vehicle type
SQL_CREATE_VEHICLE_TYPE_ENUM = """
DO $$ BEGIN
    CREATE TYPE vehicle_type AS ENUM ('sedan', 'suv', 'bike', 'luxury');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;
"""

# Table for drivers
SQL_CREATE_DRIVERS_TABLE = """
CREATE TABLE IF NOT EXISTS drivers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(), -- Using UUID for driver IDs
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE, -- Optional, but good for contact
    latitude NUMERIC(9, 6) NOT NULL, -- Storing coordinates for simplicity
    longitude NUMERIC(9, 6) NOT NULL,
    status driver_status DEFAULT 'available',
    vehicle_type vehicle_type DEFAULT 'sedan',
    price_per_km NUMERIC(5, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
"""

# Enum for order status
SQL_CREATE_ORDER_STATUS_ENUM = """
DO $$ BEGIN
    CREATE TYPE order_status AS ENUM ('pending', 'accepted', 'in_progress', 'completed', 'cancelled');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;
"""

# Table for orders (booking history)
SQL_CREATE_ORDERS_TABLE = """
CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    driver_id UUID REFERENCES drivers(id), -- Can be NULL if not yet assigned
    start_latitude NUMERIC(9, 6) NOT NULL,
    start_longitude NUMERIC(9, 6) NOT NULL,
    end_latitude NUMERIC(9, 6) NOT NULL,
    end_longitude NUMERIC(9, 6) NOT NULL,
    fare NUMERIC(10, 2), -- Can be NULL until calculated/confirmed
    status order_status DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    assigned_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);
"""

# Indexes for performance
SQL_CREATE_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_drivers_location ON drivers (latitude, longitude) WHERE status = 'available';
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders (user_id);
CREATE INDEX IF NOT EXISTS idx_orders_driver_id ON orders (driver_id);
"""

# Optional: Function and triggers to update 'updated_at' timestamp automatically
SQL_CREATE_UPDATE_TRIGGER_FUNCTION = """
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

SQL_CREATE_DRIVERS_UPDATED_AT_TRIGGER = """
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_drivers_updated_at') THEN
        CREATE TRIGGER trg_drivers_updated_at
        BEFORE UPDATE ON drivers
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;
"""

SQL_CREATE_ORDERS_UPDATED_AT_TRIGGER = """
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_orders_updated_at') THEN
        CREATE TRIGGER trg_orders_updated_at
        BEFORE UPDATE ON orders
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;
"""

# Consolidated list of all schema statements for easy execution
ALL_SCHEMA_STATEMENTS = [
    "CREATE EXTENSION IF NOT EXISTS pgcrypto;", # Ensure UUID generation function is available
    SQL_CREATE_USERS_TABLE,
    SQL_CREATE_DRIVER_STATUS_ENUM,
    SQL_CREATE_VEHICLE_TYPE_ENUM,
    SQL_CREATE_DRIVERS_TABLE,
    SQL_CREATE_ORDER_STATUS_ENUM,
    SQL_CREATE_ORDERS_TABLE,
    SQL_CREATE_INDEXES,
    SQL_CREATE_UPDATE_TRIGGER_FUNCTION,
    SQL_CREATE_DRIVERS_UPDATED_AT_TRIGGER,
    SQL_CREATE_ORDERS_UPDATED_AT_TRIGGER,
]

# Example of how to execute these from a Python script (not part of app.py)
if __name__ == "__main__":
    print("This file defines the SQL schemas.")
    print("\n--- To set up your Supabase database, execute the following in order: ---\n")
    for statement in ALL_SCHEMA_STATEMENTS:
        print(statement.strip())
        print("---")
    print("\n--- End of Schema Statements ---")
```

File Name: pricing.py
```python
import math

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates the distance between two geographical points using the Haversine formula.
    Returns distance in kilometers.
    """
    R = 6371  # Radius of Earth in kilometers

    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance

def calculate_fare(distance_km: float, price_per_km: float) -> float:
    """
    Calculates the fare based on distance and driver's price per kilometer.
    Includes a small base fare.
    """
    base_fare = 2.50 # A small base fare
    fare = base_fare + (distance_km * price_per_km)
    return round(fare, 2)

if __name__ == "__main__":
    # Example usage
    lat_user, lon_user = 34.0522, -118.2437  # Los Angeles
    lat_dest, lon_dest = 34.0600, -118.2500 # Slightly different point
    
    dist = calculate_distance(lat_user, lon_user, lat_dest, lon_dest)
    print(f"Distance between points: {dist:.2f} km")

    driver_rate = 1.20 # $1.20 per km
    fare = calculate_fare(dist, driver_rate)
    print(f"Estimated fare: ${fare:.2f}")
```

File Name: matching.py
```python
import math
from typing import List, Dict, Any
import psycopg2.extras # Needed for DictCursor

# Re-use the distance calculation logic from pricing.py
def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates the distance between two geographical points using the Haversine formula.
    Returns distance in kilometers.
    """
    R = 6371  # Radius of Earth in kilometers

    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance

def find_available_drivers(
    db_conn, # Accepts an active psycopg2 database connection
    user_latitude: float,
    user_longitude: float,
    radius_km: float = 5
) -> List[Dict[str, Any]]:
    """
    Finds available drivers within a specified radius from the user's location.
    Queries the database for 'available' drivers and then filters them by distance.
    """
    available_drivers = []
    try:
        # Use DictCursor to fetch rows as dictionaries
        with db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            # For simplicity, we'll fetch all 'available' drivers and filter in Python.
            # For high-performance, real-time matching, PostGIS extensions would be used
            # for spatial indexing and queries directly in SQL.
            cursor.execute(
                "SELECT id, name, latitude, longitude, vehicle_type, price_per_km FROM drivers WHERE status = 'available';"
            )
            drivers_from_db = cursor.fetchall()

            for driver in drivers_from_db:
                driver_lat = driver['latitude']
                driver_lon = driver['longitude']
                distance = calculate_distance(user_latitude, user_longitude, driver_lat, driver_lon)

                if distance <= radius_km:
                    driver_data = dict(driver) # Convert psycopg2.extras.DictRow to a standard dict
                    driver_data['distance_from_user'] = distance
                    available_drivers.append(driver_data)

        # Sort drivers by distance (closest first)
        available_drivers.sort(key=lambda d: d['distance_from_user'])
        return available_drivers

    except Exception as e:
        print(f"Error finding drivers: {e}")
        # In a real application, proper logging and error handling would be implemented
        return []

if __name__ == "__main__":
    print("This file defines driver matching logic, typically called by app.py.")
    print("It requires a database connection to function, so it cannot be run directly for a full demo.")
```

File Name: app.py
```python
import os
from datetime import datetime, timezone
import uuid
from flask import Flask, request, jsonify
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import DictCursor

# Local modules
import matching
import pricing
import schemas # Import schemas to potentially run initial setup

app = Flask(__name__)

# --- Supabase PostgreSQL Configuration ---
# It's crucial to use environment variables for sensitive information.
# Replace with your actual Supabase connection details.
# Example environment variables:
# SUPABASE_DB_HOST="db.YOUR_SUPABASE_PROJECT_REF.supabase.co"
# SUPABASE_DB_PORT="5432"
# SUPABASE_DB_NAME="postgres"
# SUPABASE_DB_USER="postgres"
# SUPABASE_DB_PASSWORD="YOUR_DATABASE_PASSWORD"

DB_HOST = os.environ.get("SUPABASE_DB_HOST")
DB_PORT = os.environ.get("SUPABASE_DB_PORT", "5432")
DB_NAME = os.environ.get("SUPABASE_DB_NAME")
DB_USER = os.environ.get("SUPABASE_DB_USER")
DB_PASSWORD = os.environ.get("SUPABASE_DB_PASSWORD")

# Check if all critical environment variables are set
if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
    print("CRITICAL ERROR: Supabase database credentials not fully set in environment variables.")
    print("Please set SUPABASE_DB_HOST, SUPABASE_DB_NAME, SUPABASE_DB_USER, and SUPABASE_DB_PASSWORD.")
    # In a production environment, you might want to raise an exception or exit.
    # For now, we'll try to proceed but database operations will fail.


# Connection pool for better performance and resource management
db_pool = None

def init_db_pool():
    global db_pool
    if db_pool: # Already initialized
        return

    # Only try to initialize if credentials are provided
    if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
        print("Skipping DB pool initialization due to missing credentials.")
        return

    try:
        db_pool = SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        print("Database connection pool initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize database connection pool: {e}")
        # In a production app, you might want to exit or retry
        db_pool = None # Ensure it's None if initialization fails

# Initialize the pool when the app starts.
# Using app.app_context() ensures this runs once Flask app is ready.
with app.app_context():
    init_db_pool()

def get_db_connection():
    """Retrieves a connection from the pool."""
    if db_pool:
        return db_pool.getconn()
    raise Exception("Database connection pool not initialized or credentials missing.")

def release_db_connection(conn):
    """Returns a connection to the pool."""
    if db_pool and conn:
        db_pool.putconn(conn)

# --- Routes ---

@app.route("/")
def hello():
    return "Welcome to the Supabase-powered Ride Booking Service!"

@app.route("/drivers", methods=["GET"])
def get_drivers():
    """
    Fetches a list of all drivers from the database.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute(
                "SELECT id, name, latitude, longitude, status, vehicle_type, price_per_km FROM drivers ORDER BY name;"
            )
            drivers = cursor.fetchall()
            # Convert psycopg2.extras.DictRow objects to regular dicts for JSON serialization
            drivers_list = [dict(driver) for driver in drivers]
            return jsonify(drivers_list), 200
    except Exception as e:
        print(f"Error fetching drivers: {e}")
        return jsonify({"error": "Failed to fetch drivers", "details": str(e)}), 500
    finally:
        release_db_connection(conn)

@app.route("/book", methods=["POST"])
def book_ride():
    """
    Endpoint to book a ride.
    1. Validates input.
    2. Finds available drivers near the user using matching.py.
    3. Calculates fare using pricing.py.
    4. Creates an order in the database and updates driver status.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    user_id = data.get("user_id") # Assume user_id is provided, e.g., from auth token
    start_lat = data.get("start_latitude")
    start_lon = data.get("start_longitude")
    end_lat = data.get("end_latitude")
    end_lon = data.get("end_longitude")

    if not all([user_id, start_lat, start_lon, end_lat, end_lon]):
        return jsonify({"error": "Missing required booking details (user_id, start_latitude, start_longitude, end_latitude, end_longitude)"}), 400
    
    # Validate user_id as a UUID format (optional but good practice)
    try:
        uuid.UUID(str(user_id))
    except ValueError:
        return jsonify({"error": "Invalid user_id format. Must be a UUID."}), 400

    conn = None
    try:
        conn = get_db_connection()
        
        # 1. Find available drivers
        # Pass the connection to matching.py to allow it to query the DB
        available_drivers = matching.find_available_drivers(
            db_conn=conn,
            user_latitude=start_lat,
            user_longitude=start_lon,
            radius_km=10 # Search within 10 km radius
        )

        if not available_drivers:
            return jsonify({"message": "No drivers available near your location."}), 404

        # For simplicity, assign the closest driver
        assigned_driver = available_drivers[0]
        driver_id = assigned_driver['id']
        driver_price_per_km = assigned_driver['price_per_km']

        # 2. Calculate fare
        distance_km = pricing.calculate_distance(start_lat, start_lon, end_lat, end_lon)
        estimated_fare = pricing.calculate_fare(distance_km, driver_price_per_km)

        # 3. Create an order in the database and update driver status within a transaction
        with conn.cursor() as cursor:
            # Generate UUID for the order in Python for immediate use
            order_id = uuid.uuid4() 
            current_time_utc = datetime.now(timezone.utc)

            cursor.execute(
                """
                INSERT INTO orders (id, user_id, driver_id, start_latitude, start_longitude,
                                    end_latitude, end_longitude, fare, status, created_at, updated_at, assigned_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """,
                (str(order_id), str(user_id), str(driver_id), start_lat, start_lon,
                 end_lat, end_lon, estimated_fare, 'pending',
                 current_time_utc, current_time_utc, current_time_utc)
            )

            # Update driver status to 'busy'
            cursor.execute(
                "UPDATE drivers SET status = 'busy', updated_at = %s WHERE id = %s;",
                (current_time_utc, str(driver_id))
            )

            conn.commit() # Commit the transaction if all operations succeed

        return jsonify({
            "message": "Ride booked successfully!",
            "order_id": str(order_id),
            "assigned_driver": {
                "id": str(assigned_driver['id']),
                "name": assigned_driver['name'],
                "distance_from_user_km": round(assigned_driver['distance_from_user'], 2)
            },
            "estimated_fare": estimated_fare,
            "status": "pending"
        }), 201

    except psycopg2.Error as db_error:
        if conn:
            conn.rollback() # Rollback on DB error
        print(f"Database error during booking: {db_error}")
        return jsonify({"error": "Failed to book ride due to database issue", "details": str(db_error)}), 500
    except Exception as e:
        print(f"General error during booking: {e}")
        return jsonify({"error": "Failed to book ride", "details": str(e)}), 500
    finally:
        release_db_connection(conn)

@app.route("/orders/<order_id>", methods=["GET"])
def get_order_details(order_id):
    """
    Fetches details of a specific order.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute(
                """
                SELECT
                    o.id AS order_id, o.status AS order_status, o.fare, o.created_at, o.updated_at, o.assigned_at, o.completed_at,
                    o.start_latitude, o.start_longitude, o.end_latitude, o.end_longitude,
                    u.id AS user_id, u.name AS user_name, u.email AS user_email,
                    d.id AS driver_id, d.name AS driver_name, d.vehicle_type AS driver_vehicle_type
                FROM orders o
                JOIN users u ON o.user_id = u.id
                LEFT JOIN drivers d ON o.driver_id = d.id -- LEFT JOIN as driver_id can be NULL
                WHERE o.id = %s;
                """,
                (order_id,)
            )
            order_details = cursor.fetchone()

            if order_details:
                return jsonify(dict(order_details)), 200
            else:
                return jsonify({"message": "Order not found"}), 404
    except Exception as e:
        print(f"Error fetching order details: {e}")
        return jsonify({"error": "Failed to fetch order details", "details": str(e)}), 500
    finally:
        release_db_connection(conn)

# --- Example of populating initial data (optional, for testing) ---
@app.route("/init_data", methods=["POST"])
def init_data():
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Apply schema definitions (idempotent, using IF NOT EXISTS)
            for statement in schemas.ALL_SCHEMA_STATEMENTS:
                cursor.execute(statement)

            # Insert some example users
            cursor.execute(
                """
                INSERT INTO users (id, name, email) VALUES
                ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'Alice User', 'alice@example.com'),
                ('b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'Bob User', 'bob@example.com')
                ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, email = EXCLUDED.email;
                """
            )
            # Insert some example drivers
            cursor.execute(
                """
                INSERT INTO drivers (id, name, latitude, longitude, status, vehicle_type, price_per_km) VALUES
                ('c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'Driver Alpha', 34.0522, -118.2437, 'available', 'sedan', 1.20), -- Near Los Angeles
                ('d0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14', 'Driver Beta', 34.0600, -118.2500, 'available', 'suv', 1.50), -- Near Los Angeles
                ('e0eebc99-9c0b-4ef8-bb6d-6bb9bd380a15', 'Driver Gamma', 34.1000, -118.3000, 'available', 'bike', 0.80) -- Further away
                ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude, status = EXCLUDED.status, vehicle_type = EXCLUDED.vehicle_type, price_per_km = EXCLUDED.price_per_km;
                """
            )
            conn.commit()
        return jsonify({"message": "Database schema created/updated and example data initialized/updated successfully."}), 200
    except psycopg2.Error as db_error:
        if conn:
            conn.rollback()
        print(f"Database error during data initialization: {db_error}")
        return jsonify({"error": "Failed to initialize data", "details": str(db_error)}), 500
    except Exception as e:
        print(f"General error during data initialization: {e}")
        return jsonify({"error": "Failed to initialize data", "details": str(e)}), 500
    finally:
        release_db_connection(conn)


if __name__ == "__main__":
    # For local development, you can set these environment variables directly
    # or use a .env file and a library like python-dotenv.
    # Make sure to replace placeholders with your actual Supabase credentials.
    #
    # Example for development:
    # os.environ["SUPABASE_DB_HOST"] = "db.YOUR_SUPABASE_PROJECT_REF.supabase.co"
    # os.environ["SUPABASE_DB_NAME"] = "postgres"
    # os.environ["SUPABASE_DB_USER"] = "postgres"
    # os.environ["SUPABASE_DB_PASSWORD"] = "YOUR_DATABASE_PASSWORD"
    #
    # Ensure the pool is initialized before running the app if not using app.app_context for init
    # (though app.app_context() is generally preferred for Flask setups)
    # init_db_pool() # If you want to force init here for testing outside app context

    app.run(debug=True, host='0.0.0.0', port=5000)
```