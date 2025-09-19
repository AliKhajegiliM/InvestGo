"""Momentum and trend features."""

from __future__ import annotations

from typing import Tuple

import pandas as pd

from ..utils.dates import snap_asof


def compute_momentum_features(prices: pd.DataFrame, as_of: str, benchmark: pd.DataFrame | None = None) -> Tuple[float, dict]:
    if prices is None or prices.empty:
        block = {"rs_3m": 0.0, "dma_50_over_200": 0.0, "time_since_52w_low": 0}
        return 0.0, block

    prices = prices.copy()
    prices["date"] = pd.to_datetime(prices["date"])
    prices = prices.sort_values("date")
    as_of_ts = pd.Timestamp(snap_asof(as_of))
    history = prices.loc[prices["date"] <= as_of_ts]
    if history.empty:
        block = {"rs_3m": 0.0, "dma_50_over_200": 0.0, "time_since_52w_low": 0}
        return 0.0, block

    close = history["close"].astype(float).reset_index(drop=True)
    ret_window = 63
    rs = 0.0
    if len(close) > ret_window:
        price_now = close.iloc[-1]
        price_then = close.iloc[-ret_window]
        if price_then:
            rs = (price_now / price_then) - 1

    if benchmark is not None and not benchmark.empty:
        bench = benchmark.copy()
        bench["date"] = pd.to_datetime(bench["date"])
        bench = bench.sort_values("date")
        bench_hist = bench.loc[bench["date"] <= as_of_ts]["close"].astype(float).reset_index(drop=True)
        if len(bench_hist) > ret_window:
            b_now = bench_hist.iloc[-1]
            b_then = bench_hist.iloc[-ret_window]
            if b_then:
                rs -= (b_now / b_then) - 1

    dma_50 = close.rolling(window=50, min_periods=1).mean().iloc[-1]
    dma_200 = close.rolling(window=200, min_periods=1).mean().iloc[-1]
    dma_ratio = (dma_50 / dma_200) if dma_200 else 1.0

    idx_last_low = close[::-1].idxmin()
    time_since_low = len(close) - idx_last_low - 1

    score = 0.0
    score += min(0.4, max(-0.2, rs) + 0.2) * 0.5
    score += min(0.3, max(0.0, dma_ratio - 0.8)) * 0.5
    score += min(0.3, max(0.0, min(time_since_low / 100, 1.0))) * 0.2
    score = max(0.0, min(1.0, score))

    block = {
        "rs_3m": rs,
        "dma_50_over_200": dma_ratio,
        "time_since_52w_low": int(time_since_low),
    }
    return score, block


__all__ = ["compute_momentum_features"]
