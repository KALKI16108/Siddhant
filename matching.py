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