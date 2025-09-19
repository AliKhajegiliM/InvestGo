"""Performance metrics for the SmartMoney backtester."""

from __future__ import annotations

import math
from typing import Iterable, List

import numpy as np


def CAGR(equity: Iterable[float], periods_per_year: int = 252) -> float:
    curve = np.array(list(equity), dtype=float)
    if len(curve) < 2 or curve[0] <= 0:
        return 0.0
    total_return = curve[-1] / curve[0]
    years = len(curve) / periods_per_year
    if years <= 0:
        return 0.0
    return total_return ** (1 / years) - 1


def sharpe_ratio(returns: Iterable[float], risk_free: float = 0.0, periods_per_year: int = 252) -> float:
    arr = np.array(list(returns), dtype=float)
    if len(arr) == 0:
        return 0.0
    excess = arr - risk_free / periods_per_year
    std = np.std(excess, ddof=1)
    if std == 0:
        return 0.0
    return math.sqrt(periods_per_year) * np.mean(excess) / std


def max_drawdown(equity: Iterable[float]) -> float:
    curve = np.array(list(equity), dtype=float)
    if len(curve) == 0:
        return 0.0
    running_max = np.maximum.accumulate(curve)
    drawdown = (curve - running_max) / running_max
    return float(drawdown.min())


def hit_rate(trades: List[dict], threshold: float = 0.2) -> float:
    if not trades:
        return 0.0
    hits = sum(1 for trade in trades if trade.get("max_return", 0) >= threshold)
    return hits / len(trades)


__all__ = ["CAGR", "sharpe_ratio", "max_drawdown", "hit_rate"]
