from .base import StressCalculator


class RelativeStressCalculator(StressCalculator):
    """Calculator for relative (percentage) stress"""

    def calculate_stressed_value(self, base_value: float, stress_pct: float,
                                 factor: float = 1.0) -> float:
        return base_value * (1 + stress_pct * factor)