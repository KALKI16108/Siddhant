# matching.py
# This file would contain the core logic for matching riders with available drivers,
# considering factors like proximity, driver activity status, rating, and vehicle type.
# It is not directly modified by the current requirements but would integrate with
# the driver status and location updates handled by app.py.

from typing import List, Dict
from math import radians, sin, cos, sqrt, atan2

# Assuming a Driver model similar to the one in app.py for local operations
class MockDriver:
    def __init__(self, driver_id: str, latitude: float, longitude: float, is_active: bool):
        self.driver_id = driver_id
        self.latitude = latitude
        self.longitude = longitude
        self.is_active = is_active

class MatchingEngine:
    def __init__(self):
        # In a real system, this would query the database or a real-time cache
        # For this example, we'll use a placeholder for active drivers
        pass

    def _haversine(self, lat1, lon1, lat2, lon2):
        R = 6371  # Earth radius in kilometers
        lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(radians, [lat1, lon1, lat2, lon2])

        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c

    async def find_closest_driver(
        self,
        pickup_latitude: float,
        pickup_longitude: float,
        all_drivers: List[MockDriver] # In real app, this would be fetched from DB
    ) -> Optional[MockDriver]:
        """
        Finds the closest active driver to the given pickup coordinates.
        This would typically be an asynchronous operation querying a spatial database.
        """
        closest_driver = None
        min_distance = float('inf')

        active_drivers = [d for d in all_drivers if d.is_active]

        if not active_drivers:
            return None

        for driver in active_drivers:
            distance = self._haversine(
                pickup_latitude, pickup_longitude,
                driver.latitude, driver.longitude
            )
            if distance < min_distance:
                min_distance = distance
                closest_driver = driver
        
        return closest_driver

    async def assign_driver_to_booking(self, booking_id: str, driver_id: str):
        """
        Assigns a driver to a booking. This would involve updating the 'bookings'
        table in the database.
        """
        print(f"Assigning driver {driver_id} to booking {booking_id}")
        # Placeholder for database update logic
        # In app.py, this would involve a DB session and updating Booking.assigned_driver_id
        return True

# You might have an endpoint in app.py that uses this:
# @app.post("/booking/{booking_id}/dispatch")
# async def dispatch_driver_for_booking(...):
#     matching_engine = MatchingEngine()
#     # Assume fetching available drivers from DB first
#     available_drivers_from_db = await db.execute(select(Driver).where(Driver.is_active == True))
#     closest = await matching_engine.find_closest_driver(pickup_lat, pickup_lon, available_drivers_from_db.scalars().all())
#     if closest:
#         await matching_engine.assign_driver_to_booking(booking_id, closest.driver_id)
#         return {"message": f"Driver {closest.driver_id} dispatched for booking {booking_id}"}
#     else:
#         raise HTTPException(status_code=404, detail="No active drivers found")