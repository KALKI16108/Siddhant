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