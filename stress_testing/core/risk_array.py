from dataclasses import dataclass
from typing import List
import numpy as np

from .enums import RiskDimension


@dataclass
class RiskArray:
    """Defines the risk array for stress testing"""
    dimension: RiskDimension
    values: np.ndarray
    is_relative: bool = True  # True for percentage changes, False for absolute values

    @classmethod
    def equidistant(cls, dimension: RiskDimension, n_up: int, n_down: int,
                    step_pct: float, include_base: bool = True):
        """Create equidistant risk array"""
        up_range = np.arange(1, n_up + 1) * step_pct
        down_range = np.arange(-n_down, 0) * step_pct

        if include_base:
            values = np.concatenate([down_range, [0], up_range])
        else:
            values = np.concatenate([down_range, up_range])

        return cls(dimension=dimension, values=values, is_relative=True)

    @classmethod
    def custom(cls, dimension: RiskDimension, values: List[float], is_relative: bool = True):
        """Create custom risk array"""
        return cls(dimension=dimension, values=np.array(values), is_relative=is_relative)