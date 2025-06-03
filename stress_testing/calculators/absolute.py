from .base import StressCalculator


class AbsoluteStressCalculator(StressCalculator):
    """Calculator for absolute stress"""

    def calculate_stressed_value(self, base_value: float, stress_value: float,
                                 factor: float = 1.0) -> float:
        return base_value + stress_value * factor