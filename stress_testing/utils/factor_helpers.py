from typing import Dict

from ..core import Factor


def create_beta_factor(underlying_betas: Dict[str, float],
                      benchmark_symbol: str = "SPX") -> Factor:
    """Create a beta factor for stress testing"""
    return Factor(
        name="beta",
        underlying_factors=underlying_betas,
        benchmark_symbol=benchmark_symbol
    )


def create_idiosyncratic_factor(symbol: str, factor_value: float) -> Factor:
    """Create an idiosyncratic factor for a single underlying"""
    return Factor(
        name=f"idio_{symbol}",
        underlying_factors={symbol: factor_value}
    )