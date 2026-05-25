import math
from typing import List, Dict
from schemas import Location, Driver

# --- Constants for Matching Engine ---
EARTH_RADIUS_KM = 6371.0  # Radius of Earth in kilometers
DRIVER_SEARCH_RADIUS_KM = 5.0 # Drivers must be within 5 KM of pickup
MIN_DRIVER_WALLET_BALANCE = 20.0 # Minimum wallet balance for a driver to be eligible
AVERAGE_PICKUP_SPEED_KMH = 20.0 # Average speed for driver to reach pickup location

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates the great-circle distance between two points on the Earth
    (specified in decimal degrees) using the Haversine formula.

    Args:
        lat1, lon1: Latitude and longitude of the first point.
        lat2, lon2: Latitude and longitude of the second point.

    Returns:
        The distance between the two points in kilometers.
    """
    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Haversine formula
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = EARTH_RADIUS_KM * c
    return distance

def find_nearby_drivers(
    pickup_location: Location,
    driver_list: List[Driver]
) -> List[Dict]:
    """
    Filters a list of drivers to find those who are nearby the pickup location
    and meet eligibility criteria (wallet balance).
    Calculates estimated pickup ETA and sorts matched drivers by distance.

    Args:
        pickup_location: The geographical location of the pickup point.
        driver_list: A list of all available drivers.

    Returns:
        A list of dictionaries, where each dictionary contains:
        'driver': The Driver Pydantic model.
        'distance_to_pickup_km': Distance from driver to pickup in kilometers.
        'estimated_pickup_eta_minutes': Estimated time for the driver to reach pickup in minutes.
        The list is sorted by 'distance_to_pickup_km' in ascending order.
    """
    nearby_drivers_info = []

    pickup_lat = pickup_location.latitude
    pickup_lon = pickup_location.longitude

    for driver in driver_list:
        # 1. Financial Gatekeeper: Filter out drivers with insufficient wallet balance
        if driver.wallet_balance < MIN_DRIVER_WALLET_BALANCE:
            continue

        driver_lat = driver.current_location.latitude
        driver_lon = driver.current_location.longitude

        distance_to_pickup = haversine_distance(
            pickup_lat, pickup_lon, driver_lat, driver_lon
        )

        # 2. Matching Engine: Filter by strict 5.0 KM radius
        if distance_to_pickup <= DRIVER_SEARCH_RADIUS_KM:
            # Calculate estimated pickup ETA based on average speed
            estimated_pickup_eta_minutes = (distance_to_pickup / AVERAGE_PICKUP_SPEED_KMH) * 60

            nearby_drivers_info.append({
                "driver": driver,
                "distance_to_pickup_km": round(distance_to_pickup, 2),
                "estimated_pickup_eta_minutes": round(estimated_pickup_eta_minutes, 2)
            })

    # Sort drivers by distance to pickup (closest first)
    nearby_drivers_info.sort(key=lambda x: x["distance_to_pickup_km"])

    return nearby_drivers_info