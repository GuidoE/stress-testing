"""Stress Testing Framework for Equity and Options Portfolios"""

from .core import (
    RiskDimension,
    AggregationType,
    RiskArray,
    Factor,
    StressScenario,
    StressResult,
    ScenarioResults,
)
from .engine import StressTestEngine
from .scenarios import (
    build_price_stress_scenario,
    build_price_vol_stress_scenario,
    build_epr_stress_scenario,
    build_epr_stress_scenario_custom,
)
from .utils import (
    create_beta_factor,
    create_idiosyncratic_factor,
)

__version__ = "0.1.0"

__all__ = [
    # Core classes
    "RiskDimension",
    "AggregationType",
    "RiskArray",
    "Factor",
    "StressScenario",
    "StressResult",
    "ScenarioResults",
    # Engine
    "StressTestEngine",
    # Scenario builders
    "build_price_stress_scenario",
    "build_price_vol_stress_scenario",
    "build_epr_stress_scenario",
    "build_epr_stress_scenario_custom",
    # Factor helpers
    "create_beta_factor",
    "create_idiosyncratic_factor",
]