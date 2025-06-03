from dataclasses import dataclass
from typing import Dict

from .enums import RiskDimension


@dataclass
class StressResult:
    """Results from stress testing"""
    scenario_name: str
    stress_point: Dict[RiskDimension, float]
    position_pnl: Dict[str, float]  # Position ID -> P&L
    aggregated_pnl: Dict[str, float]  # Aggregation key -> P&L
    total_pnl: float