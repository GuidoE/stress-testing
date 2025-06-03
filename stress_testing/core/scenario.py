from dataclasses import dataclass, field
from typing import Dict, List, Optional
import itertools

from .enums import RiskDimension, AggregationType
from .risk_array import RiskArray
from .factor import Factor


@dataclass
class StressScenario:
    """Defines a stress testing scenario"""
    name: str
    risk_arrays: List[RiskArray]
    factor: Optional[Factor] = None
    aggregation_type: AggregationType = AggregationType.BY_UNDERLYING
    # For idiosyncratic scenarios - maps underlying to its own risk arrays
    underlying_risk_arrays: Optional[Dict[str, List[RiskArray]]] = None

    def get_stress_points(self) -> List[Dict[RiskDimension, float]]:
        """Generate all stress points from risk arrays"""
        if self.underlying_risk_arrays:
            # For idiosyncratic scenarios, we return a special marker
            # The actual stress points will be handled per underlying
            return [{"idiosyncratic": True}]
        elif len(self.risk_arrays) == 1:
            # Single dimension
            return [{self.risk_arrays[0].dimension: val}
                    for val in self.risk_arrays[0].values]
        else:
            # Multiple dimensions - create cartesian product
            stress_points = []
            for combo in itertools.product(*[ra.values for ra in self.risk_arrays]):
                point = {}
                for i, ra in enumerate(self.risk_arrays):
                    point[ra.dimension] = combo[i]
                stress_points.append(point)
            return stress_points