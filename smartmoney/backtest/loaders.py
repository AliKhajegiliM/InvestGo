"""Utility loaders for backtesting inputs."""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

import pandas as pd

from ..utils.io import read_dataframe


def load_backtest_inputs(price_path: str | Path, signal_path: str | Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    prices = read_dataframe(price_path)
    signals = read_dataframe(signal_path)
    return prices, signals


__all__ = ["load_backtest_inputs"]
