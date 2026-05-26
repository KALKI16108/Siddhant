import random
from sqlalchemy.exc import SQLAlchemyError
from database import engine, SessionLocal, check_db_connection
from schemas import Base, User, Driver, Booking # Import Base and models from schemas

def create_all_tables():
    """Creates all tables defined in Base metadata."""
    print("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully or already exist.")
    except SQLAlchemyError as e:
        print(f"Error creating tables: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during table creation: {e}")

# Approximate coordinates for Mumbai transit hubs
MUMBAI_TRANSIT_HUBS = {
    "Bandra": {"lat": 19.0594, "lng": 72.8300},
    "Andheri": {"lat": 19.1170, "lng": 72.8465},
    "Dadar": {"lat": 19.0177, "lng": 72.8436},
    "Kurla": {"lat": 19.0700, "lng": 72.8872},
}

def seed_drivers_data(num_drivers=10):
    """Seeds the drivers table with starter profiles."""
    db = SessionLocal()
    try:
        # Check if drivers table is empty
        existing_drivers_count = db.query(Driver).count()
        if existing_drivers_count >= num_drivers:
            print(f"Drivers table already contains {existing_drivers_count} drivers. Skipping seeding.")
            return

        print(f"Seeding {num_drivers} driver profiles...")
        drivers_to_add = []
        hub_names = list(MUMBAI_TRANSIT_HUBS.keys())
        driver_names = [
            "Rajesh Sharma", "Priya Singh", "Amit Kumar", "Neha Patel", "Suresh Yadav",
            "Anjali Devi", "Ganesh Rao", "Divya Menon", "Kiran Shah", "Vijay Gupta",
            "Manoj Kumar", "Shweta Joshi"
        ]

        for i in range(num_drivers):
            name = random.choice(driver_names)
            hub_name = random.choice(hub_names)
            location = MUMBAI_TRANSIT_HUBS[hub_name]
            
            # Add some randomness to coordinates for diversity
            lat = location["lat"] + random.uniform(-0.005, 0.005)
            lng = location["lng"] + random.uniform(-0.005, 0.005)
            
            wallet = round(random.uniform(25.0, 500.0), 2) # Wallet balance > ₹20
            is_active = random.choice([True, True, False]) # More likely to be active

            driver = Driver(name=name, lat=lat, lng=lng, wallet=wallet, is_active=is_active)
            drivers_to_add.append(driver)

        db.add_all(drivers_to_add)
        db.commit()
        print(f"Successfully seeded {len(drivers_to_add)} driver profiles.")
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Error seeding drivers data: {e}")
    except Exception as e:
        db.rollback()
        print(f"An unexpected error occurred during seeding: {e}")
    finally:
        db.close()

def main():
    """Main function to run database initialization and seeding."""
    print("Starting database initialization process...")

    # 1. Verify database connection
    if not check_db_connection():
        print("Exiting due to database connection failure.")
        return

    # 2. Create tables
    create_all_tables()

    # 3. Seed drivers data
    seed_drivers_data(10)

    print("\nDatabase initialization complete.")
    print("You can now connect to your Supabase project and verify the tables and data.")

if __name__ == "__main__":
    main()