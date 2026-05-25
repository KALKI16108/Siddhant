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