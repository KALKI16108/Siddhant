import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Retrieve DATABASE_URL from environment variables
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set. Please set it before running the application.")

# Create the SQLAlchemy engine
# pool_size: The number of connections to keep open in the pool.
# max_overflow: The number of connections that can be opened beyond the pool_size.
# pool_recycle: The number of seconds after which a connection is automatically recycled.
# This is crucial for long-running applications to handle database restarts or disconnections.
engine = create_engine(
    DATABASE_URL,
    pool_size=10,        # Keep 10 connections in the pool
    max_overflow=5,      # Allow up to 5 additional connections
    pool_recycle=3600,   # Recycle connections after 1 hour (3600 seconds)
    echo=False           # Set to True to see SQL statements for debugging
)

# Create a SessionLocal class to get database sessions
# Each instance of SessionLocal will be a database session
# The 'autocommit' is usually False in web applications to allow explicit commit/rollback
# The 'autoflush' is usually True to flush changes to the database before query execution
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_db_connection():
    """Verifies the database connection."""
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        print("Database connection successful!")
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

if __name__ == "__main__":
    # This block will only run if database.py is executed directly
    print("Attempting to connect to the database...")
    check_db_connection()