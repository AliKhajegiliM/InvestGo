"""Insider accumulation features."""

from __future__ import annotations

from datetime import timedelta
from math import log1p
from typing import Tuple

import pandas as pd

from ..utils.dates import snap_asof

ROLE_WEIGHTS = {"CEO": 1.0, "CFO": 0.9, "COO": 0.8, "Director": 0.5, "Other": 0.4}


def _window_filter(df: pd.DataFrame, as_of: str, days: int) -> pd.DataFrame:
    bound = snap_asof(as_of)
    start = bound - timedelta(days=days)
    mask = (pd.to_datetime(df["trade_date"]).dt.date <= bound) & (pd.to_datetime(df["trade_date"]).dt.date >= start)
    return df.loc[mask].copy()


def _cluster_count(df: pd.DataFrame) -> Tuple[int, int]:
    if df.empty:
        return 0, 0
    unique_insiders = int(df["insider_name"].nunique())
    # Treat a "cluster" as multiple insiders participating in the same 30 day
    # lookback window.  This relaxed definition is better aligned with the
    # nightly pipeline where overlapping purchases within the rebalance period
    # signal management conviction even if trades are a few days apart.
    cluster_count = 1 if unique_insiders >= 2 else 0
    return cluster_count, unique_insiders


def _role_weight(df: pd.DataFrame) -> float:
    weights = [ROLE_WEIGHTS.get(role, ROLE_WEIGHTS["Other"]) for role in df["insider_role"].fillna("Other")]
    if not weights:
        return 0.0
    return float(sum(weights) / len(weights))


def _after_drawdown(prices: pd.DataFrame, as_of: str, threshold: float = 0.3) -> bool:
    if prices is None or prices.empty:
        return False
    prices = prices.copy()
    prices["date"] = pd.to_datetime(prices["date"]).dt.date
    bound = snap_asof(as_of)
    window = prices.loc[prices["date"] <= bound].tail(252)
    if window.empty:
        return False
    peak = window["close"].max()
    last_close = window.iloc[-1]["close"]
    if peak <= 0:
        return False
    drawdown = (peak - last_close) / peak
    return drawdown >= threshold


def compute_insider_features(transactions: pd.DataFrame, as_of: str, prices: pd.DataFrame | None = None) -> Tuple[float, dict]:
    if transactions is None or transactions.empty:
        block = {
            "net_buys_usd_30d": 0.0,
            "cluster_count_30d": 0,
            "unique_insiders_30d": 0,
            "role_weighted_score": 0.0,
            "after_drawdown": False,
            "days_since_last_buy": None,
        }
        return 0.0, block

    recent = _window_filter(transactions, as_of, 30)
    net_buys = float(recent["transaction_value"].sum())
    cluster_count, unique_insiders = _cluster_count(recent)
    role_weight = _role_weight(recent)
    last_trade = pd.to_datetime(transactions["trade_date"]).dt.date.max()
    days_since_last = (snap_asof(as_of) - last_trade).days if last_trade else None
    drawdown_flag = _after_drawdown(prices, as_of)

    score = 0.0
    if net_buys > 0:
        score += min(0.5, log1p(net_buys) / log1p(1_000_000))
    score += min(0.2, cluster_count * 0.1)
    score += min(0.2, role_weight / 5)
    if drawdown_flag:
        score += 0.1
    score = min(score, 1.0)

    block = {
        "net_buys_usd_30d": net_buys,
        "cluster_count_30d": cluster_count,
        "unique_insiders_30d": unique_insiders,
        "role_weighted_score": role_weight,
        "after_drawdown": drawdown_flag,
        "days_since_last_buy": days_since_last,
    }
    return score, block


__all__ = ["compute_insider_features", "ROLE_WEIGHTS"]
