from typing import Optional, Tuple

from ..core import (
    StressScenario,
    RiskArray,
    RiskDimension,
    Factor,
    AggregationType
)


def build_price_stress_scenario(name: str, n_up: int = 5, n_down: int = 5,
                                step_pct: float = 0.05,
                                factor: Optional[Factor] = None) -> StressScenario:
    """
    Build a simple price stress scenario

    Args:
        name: Scenario name
        n_up: Number of up steps
        n_down: Number of down steps
        step_pct: Step size as percentage
        factor: Optional factor (e.g., beta factor)

    Returns:
        StressScenario with appropriate aggregation type
    """
    risk_array = RiskArray.equidistant(
        RiskDimension.PRICE, n_up, n_down, step_pct
    )

    # Determine aggregation type based on factor
    if factor and factor.name == "beta":
        # Beta scenarios aggregate across entire portfolio
        aggregation_type = AggregationType.BY_FACTOR
    elif factor:
        # Other factors might aggregate differently
        aggregation_type = AggregationType.BY_FACTOR
    else:
        # No factor - aggregate by underlying
        aggregation_type = AggregationType.BY_UNDERLYING

    return StressScenario(
        name=name,
        risk_arrays=[risk_array],
        factor=factor,
        aggregation_type=aggregation_type
    )


def build_price_vol_stress_scenario(name: str,
                                    price_range: Tuple[int, int, float],
                                    vol_range: Tuple[int, int, float]) -> StressScenario:
    """Build a combined price and volatility stress scenario"""
    price_array = RiskArray.equidistant(
        RiskDimension.PRICE,
        price_range[0], price_range[1], price_range[2]
    )

    vol_array = RiskArray.equidistant(
        RiskDimension.VOLATILITY,
        vol_range[0], vol_range[1], vol_range[2]
    )

    return StressScenario(
        name=name,
        risk_arrays=[price_array, vol_array],
        aggregation_type=AggregationType.BY_UNDERLYING
    )