from schemas import DeliveryRequest, DeliveryPrice
import random
import math

def calculate_price(request: DeliveryRequest) -> DeliveryPrice:
    """
    Calculates the estimated price for a delivery request.
    This is a placeholder function with basic logic.
    In a real system, this would involve complex factors like:
    - Distance between origin and destination (using geo-encoding)
    - Weight and dimensions (for vehicle type, fuel, handling)
    - Urgency/delivery speed
    - Current traffic conditions
    - Dynamic pricing based on demand/supply
    - Specific routes/tolls
    """
    # Simulate distance calculation (very basic, based on string length difference)
    # A real system would use a mapping API (e.g., Google Maps, OpenStreetMap)
    distance_factor = abs(len(request.origin) - len(request.destination)) / 10 + 1
    
    # Weight and dimension factors
    weight_factor = max(1.0, request.weight_kg / 10.0) # Base price increases with weight
    
    # Simple volume calculation
    volume_cm3 = math.prod(request.dimensions_cm)
    volume_factor = max(1.0, volume_cm3 / 10000.0) # Base price increases with volume (10,000 cm3 = 10L)

    # Base price
    base_price = 5.0

    # Combine factors (this is purely illustrative)
    total_amount = base_price * distance_factor * weight_factor * volume_factor
    
    # Add a random fluctuation for realism
    total_amount *= random.uniform(0.9, 1.1)

    # Estimate duration based on distance factor (very rough)
    estimated_duration_minutes = int(30 * distance_factor + request.weight_kg * 2 + random.randint(5, 15))
    
    return DeliveryPrice(
        amount=round(total_amount, 2),
        currency="USD",
        estimated_duration_minutes=max(15, estimated_duration_minutes) # Minimum 15 minutes
    )