from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class Factor:
    """Represents a factor for stress testing"""
    name: str
    underlying_factors: Dict[str, float]  # Underlying symbol -> factor value
    benchmark_symbol: Optional[str] = None

    def get_factor(self, symbol: str) -> float:
        """Get factor value for a specific underlying"""
        return self.underlying_factors.get(symbol, 1.0)