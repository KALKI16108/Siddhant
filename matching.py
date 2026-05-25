import random
from typing import Tuple, List

# A mock list of available drivers
AVAILABLE_DRIVERS: List[str] = ["Rajesh Kumar", "Priya Sharma", "Amit Singh", "Sunita Devi", "Vikram Patel", "Seema Rao"]

def assign_driver(pickup_coords: Tuple[float, float]) -> str:
    """
    Mocks the logic for assigning a driver.

    In a real-world system, this would involve:
    1. Querying a database or real-time service for nearby available drivers.
    2. Considering factors like driver's current location, estimated time of arrival (ETA),
       driver rating, vehicle type, and current demand.
    3. Potentially using optimization algorithms to find the best match.

    For this demonstration, it simply picks a random driver from a predefined list.

    Args:
        pickup_coords (Tuple[float, float]): The coordinates of the pickup point.
                                             (Not used in this mock but would be in real logic).

    Returns:
        str: The name of the assigned driver.
    """
    return random.choice(AVAILABLE_DRIVERS)