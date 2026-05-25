# matching.py - Module for driver matching and proximity calculations
from typing import List, Optional
from haversine import haversine, Unit
from sqlalchemy.orm import Session
from .models import Driver

def find_closest_driver(
    db: Session,
    pickup_latitude: float,
    pickup_longitude: float,
    min_wallet_balance: float = 20.0
) -> Optional[Driver]:
    """
    Finds the closest active driver with a sufficient wallet balance from the database.

    Args:
        db: SQLAlchemy session.
        pickup_latitude: Latitude of the pickup location.
        pickup_longitude: Longitude of the pickup location.
        min_wallet_balance: Minimum wallet balance required for a driver to be eligible.

    Returns:
        The closest Driver object, or None if no suitable driver is found.
    """
    # Query all active drivers with sufficient wallet balance
    eligible_drivers: List[Driver] = db.query(Driver).filter(
        Driver.is_active == True,
        Driver.wallet_balance >= min_wallet_balance
    ).all()

    if not eligible_drivers:
        return None

    pickup_coords = (pickup_latitude, pickup_longitude)
    closest_driver: Optional[Driver] = None
    min_distance_km = float('inf')

    for driver in eligible_drivers:
        driver_coords = (driver.latitude, driver.longitude)
        distance = haversine(pickup_coords, driver_coords, unit=Unit.KILOMETERS)

        if distance < min_distance_km:
            min_distance_km = distance
            closest_driver = driver
            
    return closest_driver

def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates the Haversine distance between two sets of coordinates in kilometers.
    """
    coords1 = (lat1, lon1)
    coords2 = (lat2, lon2)
    return haversine(coords1, coords2, unit=Unit.KILOMETERS)