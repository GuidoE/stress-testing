from dataclasses import dataclass
from typing import Dict, List
import numpy as np


@dataclass
class StressResult:
    """Results from stress testing for a single position"""
    scenario_name: str
    position_id: str
    underlying: str
    instrument_type: str
    quantity: float
    base_value: float
    stress_points: List[float]  # The stress levels applied (e.g., [-0.2, -0.1, 0.1, 0.2])
    pnl_values: np.ndarray  # P&L values corresponding to each stress point

    def to_dict(self) -> Dict:
        """Convert to dictionary for DataFrame construction"""
        result = {
            'scenario': self.scenario_name,
            'position_id': self.position_id,
            'underlying': self.underlying,
            'instrument_type': self.instrument_type,
            'quantity': self.quantity,
            'base_value': self.base_value,
        }

        # Add P&L values with stress points as column names
        for i, stress in enumerate(self.stress_points):
            result[f'{stress:.3f}'] = self.pnl_values[i]

        return result


@dataclass
class ScenarioResults:
    """Container for all results from a single scenario"""
    scenario_name: str
    stress_points: List[float]  # Common stress points for all positions
    position_results: List[StressResult]  # One per position
    aggregation_results: Dict[str, np.ndarray]  # Underlying -> aggregated P&L array