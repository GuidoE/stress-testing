#!/usr/bin/env python3
"""Basic example of running a stress test"""

from stress_testing import (
    StressTestEngine,
    build_price_stress_scenario,
    build_epr_stress_scenario,
)
from stress_testing.instruments import Equity, Option, Portfolio, Position
from stress_testing.pricing import BlackScholesPricer


def main():
    # Create instruments
    aapl = Equity("AAPL", price=280.0)
    aapl_call = Option(
        "AAPL_CALL",
        underlying="AAPL",
        strike=285.0,
        price=3.20,
        iv=0.3,
        dte=30,
        option_type="call"
    )

    # Create portfolio
    positions = [
        Position("pos1", aapl, 100),
        Position("pos2", aapl_call, -10),
    ]
    portfolio = Portfolio(positions)

    # Set up pricing models
    pricing_models = {
        "Equity": lambda inst, **params: params['price'],
        "Option": BlackScholesPricer(),
    }

    # Create engine
    engine = StressTestEngine(portfolio, pricing_models)

    # Run simple price stress
    scenario = build_price_stress_scenario(
        "Price Stress",
        n_up=5,
        n_down=5,
        step_pct=0.05
    )

    results = engine.run_scenario(scenario)

    # Display results
    df = engine._results_to_dataframe(results)
    print(df)


if __name__ == "__main__":
    main()