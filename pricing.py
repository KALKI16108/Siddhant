# pricing.py - Module for calculating booking fare

FARE_PER_KM = 1.5
BASE_FARE = 5.0

def calculate_fare(distance_km: float) -> float:
    """
    Calculates the total fare based on the distance.
    A simple linear model: Base Fare + (Distance * Fare per KM).
    """
    if distance_km < 0:
        raise ValueError("Distance cannot be negative.")
    
    total_fare = BASE_FARE + (distance_km * FARE_PER_KM)
    return round(total_fare, 2) # Round to two decimal places