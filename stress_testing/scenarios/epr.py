from typing import Dict, Union, List
import numpy as np

from ..core import (
    StressScenario,
    RiskArray,
    RiskDimension,
    AggregationType
)


def build_epr_stress_scenario(name: str,
                              epr_map: Dict[str, float],
                              n_steps: int = 2,
                              include_base: bool = False) -> StressScenario:
    """
    Build idiosyncratic stress scenario using Expected Price Range (EPR)

    Args:
        name: Scenario name
        epr_map: Dict mapping underlying symbol to EPR percentage (e.g., {"AAPL": 0.20})
        n_steps: Number of steps between 0 and EPR (excluding base)
        include_base: Whether to include the base (0%) level

    Returns:
        StressScenario with individual risk arrays per underlying
    """
    underlying_risk_arrays = {}

    for symbol, epr in epr_map.items():
        # Create equally spaced points from -EPR to +EPR
        if n_steps > 0:
            # Create steps as fractions of EPR
            fractions = np.linspace(1 / n_steps, 1, n_steps)
            up_values = fractions * epr
            down_values = -fractions * epr

            if include_base:
                values = np.concatenate([down_values[::-1], [0], up_values])
            else:
                values = np.concatenate([down_values[::-1], up_values])
        else:
            # Just use the EPR bounds
            values = np.array([-epr, epr])

        risk_array = RiskArray(
            dimension=RiskDimension.PRICE,
            values=values,
            is_relative=True
        )

        underlying_risk_arrays[symbol] = [risk_array]

    return StressScenario(
        name=name,
        risk_arrays=[],  # Empty for global risk arrays
        underlying_risk_arrays=underlying_risk_arrays,
        aggregation_type=AggregationType.BY_UNDERLYING
    )


def build_epr_stress_scenario_custom(name: str,
                                     epr_map: Dict[str, float],
                                     grid_spec: Union[List[float], Dict[str, List[float]]]) -> StressScenario:
    """
    Build idiosyncratic stress scenario with custom grid specification

    Args:
        name: Scenario name
        epr_map: Dict mapping underlying symbol to EPR percentage
        grid_spec: Either a list of fractions to apply to all EPRs,
                  or a dict mapping symbols to their specific fractions

    Example:
        # Same grid for all
        grid_spec = [-1, -0.5, 0.5, 1]  # Will be multiplied by each symbol's EPR

        # Different grids
        grid_spec = {
            "AAPL": [-1, -0.5, 0, 0.5, 1],
            "NVDA": [-1, -0.75, -0.5, -0.25, 0.25, 0.5, 0.75, 1]
        }
    """
    underlying_risk_arrays = {}

    for symbol, epr in epr_map.items():
        if isinstance(grid_spec, dict):
            fractions = grid_spec.get(symbol, [-1, 1])  # Default to bounds only
        else:
            fractions = grid_spec

        values = np.array(fractions) * epr

        risk_array = RiskArray(
            dimension=RiskDimension.PRICE,
            values=values,
            is_relative=True
        )

        underlying_risk_arrays[symbol] = [risk_array]

    return StressScenario(
        name=name,
        risk_arrays=[],
        underlying_risk_arrays=underlying_risk_arrays,
        aggregation_type=AggregationType.BY_UNDERLYING
    )