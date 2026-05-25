import os
import random
import psycopg2
from psycopg2 import sql
from datetime import datetime
from decimal import Decimal

# --- Configuration ---
# Mumbai transit hub coordinates (approximate)
MUMBAI_HUBS = {
    "Dadar": {"latitude": 19.0176, "longitude": 72.8282},
    "Andheri": {"latitude": 19.1136, "longitude": 72.8696},
    "Kurla": {"latitude": 19.0658, "longitude": 72.8809},
    "Bandra": {"latitude": 19.0592, "longitude": 72.8402},
    "CST": {"latitude": 18.9401, "longitude": 72.8347},
}

# List of common Indian names for drivers
DRIVER_NAMES = [
    "Rajesh Kumar", "Sanjay Sharma", "Priya Singh", "Amit Patel", "Deepa Rao",
    "Mohammed Khan", "Anjali Gupta", "Vikram Yadav", "Pooja Mehta", "Rahul Desai",
    "Kavita Reddy", "Arjun Singh", "Shruti Iyer", "Ganesh Naik", "Sunita Devi"
]

def get_db_connection():
    """Establishes a connection to the PostgreSQL database using DATABASE_URL."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set.")
    
    try:
        conn = psycopg2.connect(database_url)
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to the database: {e}")
        raise

def create_drivers_table_if_not_exists(cursor):
    """Creates the 'drivers' table if it doesn't already exist."""
    create_table_query = """
    CREATE TABLE IF NOT EXISTS drivers (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        phone_number VARCHAR(15) UNIQUE NOT NULL,
        latitude DECIMAL(9,6) NOT NULL,
        longitude DECIMAL(9,6) NOT NULL,
        wallet_balance DECIMAL(10,2) NOT NULL DEFAULT 0.00,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """
    cursor.execute(create_table_query)
    print("Checked/Created 'drivers' table.")

def generate_driver_profile():
    """Generates a single realistic driver profile."""
    name = random.choice(DRIVER_NAMES)
    
    # Generate a dummy Indian phone number (starts with 6,7,8,9)
    phone_prefix = random.choice(['98', '99', '88', '89', '78', '79', '68', '69'])
    phone_number = f"+91 {phone_prefix}{random.randint(10000000, 99999999)}"

    # Pick a random hub and perturb coordinates slightly
    hub_name, hub_coords = random.choice(list(MUMBAI_HUBS.items()))
    latitude = hub_coords['latitude'] + random.uniform(-0.01, 0.01) # +/- 0.01 degrees ~ 1.1 km
    longitude = hub_coords['longitude'] + random.uniform(-0.01, 0.01)

    # Wallet balance above ₹20, up to ₹1000
    wallet_balance = Decimal(random.uniform(20.01, 1000.00)).quantize(Decimal('0.01'))
    
    return {
        "name": name,
        "phone_number": phone_number,
        "latitude": round(latitude, 6),
        "longitude": round(longitude, 6),
        "wallet_balance": wallet_balance,
        "is_active": True,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

def seed_drivers_data(num_drivers=10):
    """
    Connects to the database and inserts a specified number of driver profiles.
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        create_drivers_table_if_not_exists(cur)

        inserted_count = 0
        phone_numbers = set() # To keep track of unique phone numbers

        print(f"Attempting to insert {num_drivers} driver profiles...")
        while inserted_count < num_drivers:
            driver_data = generate_driver_profile()
            
            # Basic uniqueness check for phone number (can have collisions with random gen)
            if driver_data['phone_number'] in phone_numbers:
                continue # Regenerate if phone number already generated in this run
            
            insert_query = sql.SQL("""
                INSERT INTO drivers (
                    name, phone_number, latitude, longitude, wallet_balance, is_active, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s
                ) ON CONFLICT (phone_number) DO NOTHING;
            """)
            
            try:
                cur.execute(insert_query, (
                    driver_data['name'],
                    driver_data['phone_number'],
                    driver_data['latitude'],
                    driver_data['longitude'],
                    driver_data['wallet_balance'],
                    driver_data['is_active'],
                    driver_data['created_at'],
                    driver_data['updated_at']
                ))
                if cur.rowcount > 0: # Check if a row was actually inserted (not ON CONFLICT DO NOTHING)
                    inserted_count += 1
                    phone_numbers.add(driver_data['phone_number'])
                    print(f"Inserted driver {inserted_count}: {driver_data['name']} ({driver_data['phone_number']}) at ({driver_data['latitude']},{driver_data['longitude']}) with balance ₹{driver_data['wallet_balance']}")
                else:
                    print(f"Skipped existing driver with phone number: {driver_data['phone_number']}")

            except psycopg2.errors.UniqueViolation:
                # This could happen if a phone number generated randomly already exists in the DB
                print(f"Phone number {driver_data['phone_number']} already exists. Generating new profile...")
                conn.rollback() # Rollback the current transaction
            except psycopg2.Error as e:
                print(f"Error inserting driver: {e}")
                conn.rollback() # Rollback on other errors
                break # Exit loop if a critical error occurs
        
        conn.commit()
        print(f"\nSuccessfully inserted {inserted_count} unique driver profiles.")

    except ValueError as e:
        print(f"Configuration error: {e}")
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    # Example usage:
    # Set your DATABASE_URL environment variable before running:
    # export DATABASE_URL="postgresql://user:password@host:port/database_name"
    seed_drivers_data(num_drivers=10)