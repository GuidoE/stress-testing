from typing import Dict, List, Any, Callable, Optional, Tuple
from collections import defaultdict
import pandas as pd
import numpy as np

from ..core import (
    StressScenario,
    StressResult,
    ScenarioResults,
    Factor,
    RiskDimension,
    AggregationType
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

    def run_scenario(self, scenario: StressScenario) -> ScenarioResults:
        """Run a single stress scenario"""
        if scenario.underlying_risk_arrays:
            return self._run_idiosyncratic_scenario(scenario)

        # Get stress points and convert to simple list
        stress_points = scenario.get_stress_points()

        # For single dimension scenarios, extract the values
        if len(scenario.risk_arrays) == 1:
            dimension = scenario.risk_arrays[0].dimension
            stress_values = [pt[dimension] for pt in stress_points]
        else:
            # For multi-dimensional, we'll need a different approach
            # For now, handle price dimension if it exists
            stress_values = []
            for pt in stress_points:
                if RiskDimension.PRICE in pt:
                    stress_values.append(pt[RiskDimension.PRICE])
                else:
                    # Use first dimension value
                    stress_values.append(list(pt.values())[0])

        position_results = []

        # Process each position
        for position in self.portfolio.positions:
            pnl_values = []

            # Calculate P&L for each stress point
            for stress_point in stress_points:
                # Get base parameters
                base_params = self._get_instrument_params(position.instrument)

                # Apply stress to parameters
                stressed_params = self._apply_stress(
                    base_params,
                    stress_point,
                    position.instrument,
                    scenario.factor
                )

                # Calculate stressed value
                stressed_value = self._price_instrument(
                    position.instrument,
                    stressed_params
                )

                # Calculate P&L
                base_value = position.quantity * position.instrument.price
                stressed_total = position.quantity * stressed_value
                pnl = stressed_total - base_value
                pnl_values.append(pnl)

            # Create result for this position
            result = StressResult(
                scenario_name=scenario.name,
                position_id=position.id,
                underlying=self._get_underlying_symbol(position.instrument),
                instrument_type=type(position.instrument).__name__,
                quantity=position.quantity,
                base_value=position.quantity * position.instrument.price,
                stress_points=stress_values,
                pnl_values=np.array(pnl_values)
            )
            position_results.append(result)

        # Calculate aggregated results
        aggregation_results = self._calculate_aggregation(position_results, scenario.aggregation_type)

        return ScenarioResults(
            scenario_name=scenario.name,
            stress_points=stress_values,
            position_results=position_results,
            aggregation_results=aggregation_results
        )

    def _run_idiosyncratic_scenario(self, scenario: StressScenario) -> ScenarioResults:
        """Run idiosyncratic stress scenario where each underlying has its own risk array"""
        position_results = []
        all_stress_fractions = None  # Will store common fractions for display

        # First, determine common stress fractions for display purposes
        # Assuming all underlyings use the same fractions of their EPR
        for underlying, risk_arrays in scenario.underlying_risk_arrays.items():
            if len(risk_arrays) > 0 and risk_arrays[0].dimension == RiskDimension.PRICE:
                # Get the first underlying's risk array to determine fractions
                first_epr = next(iter(scenario.underlying_risk_arrays.values()))[0]
                if all_stress_fractions is None:
                    # Normalize to get fractions (assuming symmetric around 0)
                    max_val = np.max(np.abs(first_epr.values))
                    if max_val > 0:
                        all_stress_fractions = (first_epr.values / max_val).tolist()
                break

        if all_stress_fractions is None:
            all_stress_fractions = [-1, 1]  # Default

        # Group positions by underlying
        positions_by_underlying = defaultdict(list)
        for position in self.portfolio.positions:
            underlying = self._get_underlying_symbol(position.instrument)
            positions_by_underlying[underlying].append(position)

        # Process each position
        for position in self.portfolio.positions:
            underlying = self._get_underlying_symbol(position.instrument)

            # Get risk arrays for this underlying
            if underlying not in scenario.underlying_risk_arrays:
                # No stress defined for this underlying, use zero stress
                pnl_values = np.zeros(len(all_stress_fractions))
            else:
                risk_arrays = scenario.underlying_risk_arrays[underlying]

                # Get stress points for this underlying
                if len(risk_arrays) == 1:
                    stress_values = risk_arrays[0].values
                else:
                    # Handle multi-dimensional case if needed
                    stress_values = risk_arrays[0].values  # Simplified for now

                pnl_values = []

                # Calculate P&L for each stress point
                for stress_value in stress_values:
                    base_params = self._get_instrument_params(position.instrument)

                    # Create stress point
                    stress_point = {RiskDimension.PRICE: stress_value}

                    stressed_params = self._apply_stress(
                        base_params,
                        stress_point,
                        position.instrument,
                        scenario.factor
                    )

                    stressed_value = self._price_instrument(
                        position.instrument,
                        stressed_params
                    )

                    base_value = position.quantity * position.instrument.price
                    stressed_total = position.quantity * stressed_value
                    pnl = stressed_total - base_value
                    pnl_values.append(pnl)

            # Create result for this position
            result = StressResult(
                scenario_name=f"{scenario.name}",
                position_id=position.id,
                underlying=underlying,
                instrument_type=type(position.instrument).__name__,
                quantity=position.quantity,
                base_value=position.quantity * position.instrument.price,
                stress_points=all_stress_fractions,
                pnl_values=np.array(pnl_values)
            )
            position_results.append(result)

        # Calculate aggregated results
        aggregation_results = self._calculate_aggregation(position_results, scenario.aggregation_type)

        return ScenarioResults(
            scenario_name=scenario.name,
            stress_points=all_stress_fractions,
            position_results=position_results,
            aggregation_results=aggregation_results
        )

    def run_scenarios(self, scenarios: List[StressScenario]) -> Dict[str, pd.DataFrame]:
        """
        Run multiple scenarios and return results as separate DataFrames

        Returns:
            Dict mapping scenario name to its DataFrame
        """
        results_dict = {}

        for scenario in scenarios:
            scenario_results = self.run_scenario(scenario)
            df = self._scenario_results_to_dataframe(scenario_results)
            results_dict[scenario.name] = df

        return results_dict

    def _calculate_aggregation(self, position_results: List[StressResult],
                               aggregation_type: AggregationType) -> Dict[str, np.ndarray]:
        """Calculate aggregated P&L arrays"""
        aggregated = defaultdict(lambda: None)

        if aggregation_type == AggregationType.BY_UNDERLYING:
            # Group by underlying
            for result in position_results:
                if aggregated[result.underlying] is None:
                    aggregated[result.underlying] = np.zeros_like(result.pnl_values)
                aggregated[result.underlying] += result.pnl_values

        elif aggregation_type == AggregationType.TOTAL:
            # Single total aggregation
            total = np.zeros_like(position_results[0].pnl_values)
            for result in position_results:
                total += result.pnl_values
            aggregated['total'] = total

        return dict(aggregated)

    def _scenario_results_to_dataframe(self, scenario_results: ScenarioResults) -> pd.DataFrame:
        """Convert ScenarioResults to DataFrame with P&L values as columns"""
        data = []

        # Add position results
        for result in scenario_results.position_results:
            row = result.to_dict()
            data.append(row)

        # Add aggregation results
        for underlying, pnl_array in scenario_results.aggregation_results.items():
            row = {
                'scenario': scenario_results.scenario_name,
                'position_id': f'AGG_{underlying}',
                'underlying': underlying,
                'instrument_type': 'AGGREGATE',
                'quantity': '',
                'base_value': '',
            }

            # Add P&L values
            for i, stress in enumerate(scenario_results.stress_points):
                row[f'{stress:.3f}'] = pnl_array[i]

            data.append(row)

        # Create DataFrame
        df = pd.DataFrame(data)

        # Reorder columns to put P&L columns at the end
        meta_cols = ['scenario', 'underlying', 'position_id', 'instrument_type', 'quantity', 'base_value']
        pnl_cols = [col for col in df.columns if col not in meta_cols]
        df = df[meta_cols + pnl_cols]

        return df

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