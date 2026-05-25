import math
from typing import Tuple

def calculate_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """
    Calculates the great-circle distance between two points on the Earth
    (specified in decimal degrees) using the Haversine formula.

    Args:
        p1 (Tuple[float, float]): (latitude, longitude) of the first point.
        p2 (Tuple[float, float]): (latitude, longitude) of the second point.

    Returns:
        float: Distance in kilometers.
    """
    R = 6371  # Earth radius in kilometers

    lat1, lon1 = math.radians(p1[0]), math.radians(p1[1])
    lat2, lon2 = math.radians(p2[0]), math.radians(p2[1])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance

def calculate_fare(pickup_coords: Tuple[float, float], dropoff_coords: Tuple[float, float]) -> float:
    """
    Calculates a mock fare based on distance between pickup and dropoff points.

    Args:
        pickup_coords (Tuple[float, float]): (latitude, longitude) of pickup.
        dropoff_coords (Tuple[float, float]): (latitude, longitude) of dropoff.

    Returns:
        float: Rounded total fare.
    """
    distance_km = calculate_distance(pickup_coords, dropoff_coords)

    # Simple pricing model
    base_fare = 50.0  # INR
    per_km_rate = 15.0 # INR/km
    minimum_fare_distance_km = 1.0 # Minimum distance for full per_km_rate

    effective_distance_km = max(distance_km, minimum_fare_distance_km)
    fare = base_fare + (effective_distance_km * per_km_rate)

    # Add a surge factor for demonstration (e.g., random 1.0 to 1.5x)
    # surge_factor = 1.0 + (random.random() * 0.5)
    # fare *= surge_factor

    return round(fare, 2)