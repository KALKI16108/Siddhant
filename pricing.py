import math

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

def calculate_fare(distance_km: float, price_per_km: float) -> float:
    """
    Calculates the fare based on distance and driver's price per kilometer.
    Includes a small base fare.
    """
    base_fare = 2.50 # A small base fare
    fare = base_fare + (distance_km * price_per_km)
    return round(fare, 2)

if __name__ == "__main__":
    # Example usage
    lat_user, lon_user = 34.0522, -118.2437  # Los Angeles
    lat_dest, lon_dest = 34.0600, -118.2500 # Slightly different point
    
    dist = calculate_distance(lat_user, lon_user, lat_dest, lon_dest)
    print(f"Distance between points: {dist:.2f} km")

    driver_rate = 1.20 # $1.20 per km
    fare = calculate_fare(dist, driver_rate)
    print(f"Estimated fare: ${fare:.2f}")