from abc import ABC, abstractmethod


class StressCalculator(ABC):
    """Abstract base class for stress calculations"""

    @abstractmethod
    def calculate_stressed_value(self, base_value: float, stress_pct: float,
                                 factor: float = 1.0) -> float:
        """Calculate stressed value given base value and stress percentage"""
        pass