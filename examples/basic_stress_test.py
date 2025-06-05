"""
Example demonstrating the new results format for stress testing
"""

from dataclasses import dataclass
from stress_testing import (
    StressTestEngine,
    build_price_stress_scenario,
    build_epr_stress_scenario,
    create_beta_factor
)


# Example instrument classes (placeholders for your actual classes)
@dataclass
class Equity:
    symbol: str
    price: float


@dataclass
class Option:
    underlying: str
    strike: float
    price: float
    iv: float
    dte: int
    option_type: str


@dataclass
class Position:
    id: str
    instrument: object
    quantity: float


@dataclass
class Portfolio:
    positions: list


def example_basic_stress_test():
    """Example of basic stress test with new results format"""

    # Create instruments
    aapl = Equity("AAPL", price=280.0)
    aapl_call = Option(
        underlying="AAPL",
        strike=285.0,
        price=3.20,
        iv=0.3,
        dte=30,
        option_type="call"
    )
    msft = Equity("MSFT", price=400.0)

    # Create portfolio
    positions = [
        Position("pos1", aapl, 100),
        Position("pos2", aapl_call, -10),
        Position("pos3", msft, 50),
    ]
    portfolio = Portfolio(positions)

    # Simple pricing models
    def equity_pricer(inst, **params):
        return params['price']

    def option_pricer(inst, **params):
        # Simplified - just apply price change to option
        return inst.price * (params['price'] / inst.price)

    pricing_models = {
        'Equity': equity_pricer,
        'Option': option_pricer
    }

    # Create engine
    engine = StressTestEngine(portfolio, pricing_models)

    # Run simple price stress
    scenario = build_price_stress_scenario(
        "Price Stress",
        n_up=2,
        n_down=2,
        step_pct=0.05
    )

    # Run single scenario - returns ScenarioResults
    results = engine.run_scenario(scenario)

    # Convert to DataFrame
    df = engine._scenario_results_to_dataframe(results)

    print("Single Scenario Results:")
    print(df)
    print("\n")

    return df


def example_epr_stress_test():
    """Example of EPR stress test with idiosyncratic moves"""

    # Create instruments
    aapl = Equity("AAPL", price=280.0)
    msft = Equity("MSFT", price=400.0)
    nvda = Equity("NVDA", price=800.0)

    # Create portfolio
    positions = [
        Position("pos1", aapl, 300),
        Position("pos2", msft, 200),
        Position("pos3", nvda, 100),
    ]
    portfolio = Portfolio(positions)

    # Pricing model
    pricing_models = {
        'Equity': lambda inst, **params: params['price']
    }

    # Create engine
    engine = StressTestEngine(portfolio, pricing_models)

    # Define EPRs
    epr_map = {
        "AAPL": 0.20,  # 20% EPR
        "MSFT": 0.15,  # 15% EPR
        "NVDA": 0.40  # 40% EPR
    }

    # Create EPR scenario
    epr_scenario = build_epr_stress_scenario(
        name="1-Day EPR Stress",
        epr_map=epr_map,
        n_steps=2,
        include_base=False
    )

    # Run scenario
    results = engine.run_scenario(epr_scenario)
    df = engine._scenario_results_to_dataframe(results)

    print("EPR Scenario Results:")
    print(df)
    print("\n")

    # Note how each position has P&L calculated based on its own EPR
    # Headers show fractions: -1.000, -0.500, 0.500, 1.000
    # But actual stress applied is fraction × EPR for each underlying

    return df


def example_multiple_scenarios():
    """Example running multiple scenarios and getting separate DataFrames"""

    # Create portfolio
    aapl = Equity("AAPL", price=280.0)
    msft = Equity("MSFT", price=400.0)

    positions = [
        Position("pos1", aapl, 100),
        Position("pos2", msft, 50),
    ]
    portfolio = Portfolio(positions)

    pricing_models = {'Equity': lambda inst, **params: params['price']}
    engine = StressTestEngine(portfolio, pricing_models)

    # Create multiple scenarios
    scenarios = [
        build_price_stress_scenario("Small Moves", n_up=3, n_down=3, step_pct=0.02),
        build_price_stress_scenario("Large Moves", n_up=2, n_down=2, step_pct=0.10),
        build_epr_stress_scenario("EPR Stress", {"AAPL": 0.20, "MSFT": 0.15}, n_steps=2)
    ]

    # Run all scenarios - returns dict of DataFrames
    results_dict = engine.run_scenarios(scenarios)

    # Each scenario gets its own DataFrame
    for scenario_name, df in results_dict.items():
        print(f"\n{scenario_name} Results:")
        print(df)
        print("-" * 80)

    return results_dict


def example_results_interpretation():
    """Show how to interpret the new results format"""

    # Simple 2-position portfolio
    positions = [
        Position("AAPL_100", Equity("AAPL", 150.0), 100),
        Position("MSFT_50", Equity("MSFT", 300.0), 50),
    ]
    portfolio = Portfolio(positions)

    pricing_models = {'Equity': lambda inst, **params: params['price']}
    engine = StressTestEngine(portfolio, pricing_models)

    # 5% up/down stress
    scenario = build_price_stress_scenario("5% Stress", n_up=1, n_down=1, step_pct=0.05)
    results = engine.run_scenario(scenario)
    df = engine._scenario_results_to_dataframe(results)

    print("Results DataFrame:")
    print(df)
    print("\n")

    print("How to read the results:")
    print("- Each row is a position (plus aggregated rows)")
    print("- Columns -0.050 and 0.050 show P&L at -5% and +5% stress")
    print("- AAPL position (100 shares @ $150):")
    print("  - At -5%: P&L = 100 * (150 * 0.95 - 150) = -$750")
    print("  - At +5%: P&L = 100 * (150 * 1.05 - 150) = +$750")
    print("- Aggregated rows show total P&L by underlying")

    return df


if __name__ == "__main__":
    # Run examples
    print("=" * 80)
    print("STRESS TESTING FRAMEWORK - NEW RESULTS FORMAT")
    print("=" * 80)

    example_basic_stress_test()
    example_epr_stress_test()
    example_multiple_scenarios()
    example_results_interpretation()