from typing import Dict, List, Callable, Any, Optional
from collections import defaultdict
import pandas as pd
import itertools

from ..core import (
    StressScenario,
    StressResult,
    RiskDimension,
    AggregationType,
    Factor
)
from ..calculators import RelativeStressCalculator, AbsoluteStressCalculator


class StressTestEngine:
    """Main engine for running stress tests"""

    def __init__(self, portfolio, pricing_models: Dict[str, Callable]):
        """
        Initialize stress test engine

        Args:
            portfolio: Portfolio object containing positions
            pricing_models: Dict mapping instrument type to pricing function
        """
        self.portfolio = portfolio
        self.pricing_models = pricing_models
        self.stress_calculators = {
            True: RelativeStressCalculator(),
            False: AbsoluteStressCalculator()
        }

    def _calculate_position_pnl(self, positions: List, stress_point: dict, scenario_factor: float) -> dict:
        """Calculate P&L for a list of positions under stress"""
        position_pnl = {}
        
        for position in positions:
            base_params = self._get_instrument_params(position.instrument)
            
            stressed_params = self._apply_stress(
                base_params,
                stress_point,
                position.instrument,
                scenario_factor
            )
            
            stressed_value = self._price_instrument(
                position.instrument,
                stressed_params
            )
            
            base_value = position.quantity * position.instrument.price
            stressed_total = position.quantity * stressed_value
            position_pnl[position.id] = stressed_total - base_value
        
        return position_pnl

    def _generate_stress_points(self, risk_arrays: List) -> List[dict]:
        """Generate stress points from risk arrays"""
        if len(risk_arrays) == 1:
            return [{risk_arrays[0].dimension: val} for val in risk_arrays[0].values]
        else:
            # Multiple dimensions
            stress_points = []
            for combo in itertools.product(*[ra.values for ra in risk_arrays]):
                point = {}
                for i, ra in enumerate(risk_arrays):
                    point[ra.dimension] = combo[i]
                stress_points.append(point)
            return stress_points

    def _run_idiosyncratic_scenario(self, scenario: StressScenario) -> List[StressResult]:
        """Run idiosyncratic stress scenario where each underlying has its own risk array"""
        results = []

        # Group positions by underlying
        positions_by_underlying = defaultdict(list)
        for position in self.portfolio.positions:
            underlying = self._get_underlying_symbol(position.instrument)
            positions_by_underlying[underlying].append(position)

        # For each underlying, run its specific stress tests
        for underlying, risk_arrays in scenario.underlying_risk_arrays.items():
            if underlying not in positions_by_underlying:
                continue

            # Get stress points for this underlying
            underlying_stress_points = self._generate_stress_points(risk_arrays)

            # Run stress for each point
            for stress_point in underlying_stress_points:
                # Only stress positions for this underlying
                position_pnl = self._calculate_position_pnl(
                    positions_by_underlying[underlying], 
                    stress_point, 
                    scenario.factor
                )

            # For idiosyncratic scenarios, aggregate by underlying
            aggregated_pnl = {underlying: sum(position_pnl.values())}

            # Add underlying identifier to stress point for clarity
            stress_point_with_underlying = stress_point.copy()
            stress_point_with_underlying['underlying'] = underlying

            result = StressResult(
                scenario_name=f"{scenario.name}_{underlying}",
                stress_point=stress_point_with_underlying,
                position_pnl=position_pnl,
                aggregated_pnl=aggregated_pnl,
                total_pnl=sum(position_pnl.values())
            )
            results.append(result)

        return results

    def run_scenario(self, scenario: StressScenario) -> List[StressResult]:
        """Run stress scenario and return results"""
        if scenario.is_idiosyncratic:
            return self._run_idiosyncratic_scenario(scenario)
    
        results = []
    
        # Generate stress points for all risk arrays
        stress_points = self._generate_stress_points(scenario.risk_arrays)
    
        # Run stress for each point
        for stress_point in stress_points:
            # Calculate P&L for all positions
            position_pnl = self._calculate_position_pnl(
                self.portfolio.positions, 
                stress_point, 
                scenario.factor
            )
        
            # Aggregate results (implementation depends on your aggregation logic)
            aggregated_pnl = self._aggregate_pnl(position_pnl)
        
            result = StressResult(
                scenario_name=scenario.name,
                stress_point=stress_point,
                position_pnl=position_pnl,
                aggregated_pnl=aggregated_pnl,
                total_pnl=sum(position_pnl.values())
            )
            results.append(result)
    
        return results

    def run_scenarios(self, scenarios: List[StressScenario]) -> pd.DataFrame:
        """Run multiple scenarios and return results as DataFrame"""
        all_results = []

        for scenario in scenarios:
            results = self.run_scenario(scenario)
            all_results.extend(results)

        # Convert to DataFrame for easy analysis
        return self._results_to_dataframe(all_results)

    def _get_instrument_params(self, instrument) -> Dict[str, Any]:
        """Extract parameters from instrument"""
        params = {}

        if hasattr(instrument, 'price'):
            params['price'] = instrument.price
        if hasattr(instrument, 'iv'):
            params['volatility'] = instrument.iv
        if hasattr(instrument, 'dte'):
            params['time'] = instrument.dte
        if hasattr(instrument, 'risk_free'):
            params['interest_rate'] = instrument.risk_free
        if hasattr(instrument, 'yield'):
            params['dividend_yield'] = instrument.dividend_yield

        return params

    def _apply_stress(self, base_params: Dict[str, Any],
                      stress_point: Dict[RiskDimension, float],
                      instrument, factor: Optional[Factor]) -> Dict[str, Any]:
        """Apply stress to instrument parameters"""
        stressed_params = base_params.copy()

        for dimension, stress_value in stress_point.items():
            param_name = dimension.value

            if param_name in base_params:
                # Get factor value if applicable
                factor_value = 1.0
                if factor and hasattr(instrument, 'underlying'):
                    factor_value = factor.get_factor(instrument.underlying)
                elif factor and hasattr(instrument, 'symbol'):
                    factor_value = factor.get_factor(instrument.symbol)

                # Apply stress based on dimension
                if dimension == RiskDimension.TIME:
                    # Time decay - subtract days
                    stressed_params[param_name] = max(
                        0,
                        base_params[param_name] - stress_value
                    )
                else:
                    # Apply relative stress
                    calculator = self.stress_calculators[True]
                    stressed_params[param_name] = calculator.calculate_stressed_value(
                        base_params[param_name],
                        stress_value,
                        factor_value
                    )

        return stressed_params

    def _price_instrument(self, instrument, params: Dict[str, Any]) -> float:
        """Price instrument with given parameters"""
        instrument_type = type(instrument).__name__

        if instrument_type in self.pricing_models:
            return self.pricing_models[instrument_type](instrument, **params)
        else:
            # Default: just return the price parameter
            return params.get('price', 0)

    def _aggregate_pnl(self, position_pnl: Dict[str, float],
                       aggregation_type: AggregationType,
                       factor: Optional[Factor]) -> Dict[str, float]:
        """Aggregate P&L based on aggregation type"""
        aggregated = defaultdict(float)

        if aggregation_type == AggregationType.TOTAL:
            aggregated['total'] = sum(position_pnl.values())

        elif aggregation_type == AggregationType.BY_UNDERLYING:
            # Group by underlying symbol
            for position_id, pnl in position_pnl.items():
                position = self._get_position_by_id(position_id)
                if position:
                    underlying = self._get_underlying_symbol(position.instrument)
                    aggregated[underlying] += pnl

        elif aggregation_type == AggregationType.BY_FACTOR:
            # Group by factor (e.g., all positions affected by same factor)
            if factor:
                aggregated[factor.name] = sum(position_pnl.values())
            else:
                aggregated['no_factor'] = sum(position_pnl.values())

        return dict(aggregated)

    def _get_position_by_id(self, position_id: str):
        """Get position by ID from portfolio"""
        for position in self.portfolio.positions:
            if position.id == position_id:
                return position
        return None

    def _get_underlying_symbol(self, instrument) -> str:
        """Get underlying symbol from instrument"""
        if hasattr(instrument, 'underlying'):
            return instrument.underlying
        elif hasattr(instrument, 'symbol'):
            return instrument.symbol
        else:
            return 'unknown'

    def _results_to_dataframe(self, results: List[StressResult]) -> pd.DataFrame:
        """Convert results to DataFrame for analysis"""
        data = []

        for result in results:
            row = {
                'scenario': result.scenario_name,
                'total_pnl': result.total_pnl
            }

            # Add stress dimensions
            for dim, value in result.stress_point.items():
                if isinstance(dim, RiskDimension):
                    row[f'stress_{dim.value}'] = value
                else:
                    row[f'stress_{dim}'] = value

            # Add aggregated P&L
            for key, pnl in result.aggregated_pnl.items():
                row[f'pnl_{key}'] = pnl

            data.append(row)

        return pd.DataFrame(data)