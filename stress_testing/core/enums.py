from enum import Enum


class AggregationType(Enum):
    """Types of aggregation for P&L results"""
    BY_UNDERLYING = "by_underlying"
    BY_FACTOR = "by_factor"
    TOTAL = "total"


class RiskDimension(Enum):
    """Available risk dimensions for stressing"""
    PRICE = "price"
    VOLATILITY = "volatility"
    TIME = "time"
    INTEREST_RATE = "interest_rate"
    DIVIDEND_YIELD = "dividend_yield"