import datetime

# --- Constants for Pricing Rules ---
BASE_FARE_FLAT_DISTANCE_KM = 2.0
BASE_FARE_AMOUNT = 45.0
PER_KM_RATE_AFTER_BASE = 8.00
TRAFFIC_SURCHARGE_AMOUNT = 20.0
TRAFFIC_SURCHARGE_START_HOUR = 17  # 5 PM
TRAFFIC_SURCHARGE_END_HOUR = 20    # 8 PM (exclusive, so up to 7:59:59 PM)
TRAFFIC_KEYWORDS = ['bkc', 'bandra kurla complex', 'saki naka', 'lower parel']

def calculate_fare(
    distance_km: float,
    pickup_text: str,
    drop_text: str,
    evaluation_timestamp: datetime.datetime
) -> dict:
    """
    Calculates the total fare based on distance, traffic conditions, and time of day.

    Args:
        distance_km: The total estimated distance for the delivery in kilometers.
        pickup_text: The street address text of the pickup location (for keyword matching).
        drop_text: The street address text of the drop-off location (for keyword matching).
        evaluation_timestamp: The datetime object representing when the fare is being evaluated,
                              used for checking peak hour surcharges.

    Returns:
        A dictionary containing the breakdown of the fare:
        'total_fare', 'base_fare', 'per_km_fare', 'surcharge', all rounded to two decimal places.
    """
    base_fare = 0.0
    per_km_fare = 0.0
    surcharge = 0.0

    # 1. Base Fare Calculation
    if distance_km <= BASE_FARE_FLAT_DISTANCE_KM:
        base_fare = BASE_FARE_AMOUNT
    else:
        base_fare = BASE_FARE_AMOUNT
        remaining_distance = distance_km - BASE_FARE_FLAT_DISTANCE_KM
        per_km_fare = remaining_distance * PER_KM_RATE_AFTER_BASE

    # 2. Traffic Surcharge Calculation
    current_hour = evaluation_timestamp.hour
    if TRAFFIC_SURCHARGE_START_HOUR <= current_hour < TRAFFIC_SURCHARGE_END_HOUR:
        pickup_text_lower = pickup_text.lower()
        drop_text_lower = drop_text.lower()
        
        is_traffic_zone = False
        for keyword in TRAFFIC_KEYWORDS:
            if keyword in pickup_text_lower or keyword in drop_text_lower:
                is_traffic_zone = True
                break
        
        if is_traffic_zone:
            surcharge = TRAFFIC_SURCHARGE_AMOUNT

    total_fare = base_fare + per_km_fare + surcharge

    return {
        "total_fare": round(total_fare, 2),
        "base_fare": round(base_fare, 2),
        "per_km_fare": round(per_km_fare, 2),
        "surcharge": round(surcharge, 2)
    }