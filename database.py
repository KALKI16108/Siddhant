import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load environment variables from .env file for local development
load_dotenv()

# Safely read DATABASE_URL from environment secrets
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set.")

# Initialize SQLAlchemy Engine
# The `connect_args` might be needed for some specific database setups,
# but usually not required for standard Supabase connections with psycopg2.
# For Supabase, the URL typically includes SSL parameters if needed, or it's handled automatically.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True # Ensures connections are valid
)

# Create a SessionLocal class
# Each instance of the SessionLocal class will be a database session.
# The `autocommit=False` means that we have to explicitly commit our changes,
# which is good practice for transactions.
# The `autoflush=False` means that ORM operations won't flush to the database automatically
# until a commit or an explicit flush.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declare a Base for our declarative models
# This will be imported by our models.py to define table structures.
Base = declarative_base()

def get_db():
    """
    Dependency to provide a database session for FastAPI endpoints.
    It ensures the session is closed after the request is processed.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Example: Function to create all tables (for initial setup/migrations)
def create_db_and_tables():
    """
    Creates all defined tables in the database.
    This should typically be part of a migration strategy (e.g., Alembic),
    but for a simple setup, it can be run manually or on application startup.
    """
    # Import models to ensure Base knows about them before creating tables
    # pylint: disable=unused-import,import-outside-toplevel
    from . import models
    Base.metadata.create_all(bind=engine)
    print("Database tables created (if they didn't exist).")

if __name__ == '__main__':
    # This block allows you to run `python database.py` to create tables
    # Make sure your DATABASE_URL is set in a .env file or environment.
    create_db_and_tables()
    print(f"Connected to database: {DATABASE_URL.split('@')[-1]}")