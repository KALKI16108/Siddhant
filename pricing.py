# pricing.py
# This file would contain logic related to calculating trip fares,
# surge pricing, discounts, and other financial aspects of bookings.
# It is not directly modified by the current requirements but would be part
# of a complete ride-sharing backend system.

class PricingService:
    def calculate_fare(self, distance_km: float, duration_minutes: float, base_fare: float = 2.50) -> float:
        """
        Calculates a basic fare based on distance and duration.
        In a real system, this would be much more complex, considering
        time of day, demand, vehicle type, tolls, etc.
        """
        price_per_km = 1.20
        price_per_minute = 0.20
        fare = base_fare + (distance_km * price_per_km) + (duration_minutes * price_per_minute)
        return round(fare, 2)

    def apply_surge(self, original_fare: float, surge_multiplier: float) -> float:
        """
        Applies a surge multiplier to the fare.
        """
        return round(original_fare * surge_multiplier, 2)

# You might have endpoints in app.py that call this service, e.g.:
# @app.post("/booking/{booking_id}/estimate-fare")
# async def get_fare_estimate(...):
#     pricing_service = PricingService()
#     fare = pricing_service.calculate_fare(...)
#     return {"estimated_fare": fare}