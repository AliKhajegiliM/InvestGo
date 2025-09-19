"""Simple point-in-time backtesting engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import pandas as pd

from ..types import BacktestResult
from .metrics import CAGR, hit_rate, max_drawdown, sharpe_ratio


@dataclass(slots=True)
class BacktestConfig:
    rebalance_days: int = 30
    top_k: int = 15
    cost_bps: int = 10
    slippage_bps: int = 10


@dataclass(slots=True)
class Trade:
    ticker: str
    entry_date: pd.Timestamp
    exit_date: pd.Timestamp
    entry_price: float
    exit_price: float
    max_return: float


def run_backtest(prices: pd.DataFrame, signals: pd.DataFrame, config: BacktestConfig | None = None) -> BacktestResult:
    config = config or BacktestConfig()
    prices = prices.copy()
    prices["date"] = pd.to_datetime(prices["date"])
    prices = prices.sort_values("date")
    signals = signals.copy()
    signals["as_of"] = pd.to_datetime(signals["as_of"])

    price_pivot = prices.pivot(index="date", columns="ticker", values="close").ffill()
    rebalances = sorted(signals["as_of"].unique())
    if not rebalances:
        return BacktestResult(equity_curve=[1.0], metrics={}, trades=[])

    equity_curve: List[float] = []
    daily_returns: List[float] = []
    trades: List[Dict[str, object]] = []

    equity = 1.0

    for idx, rebalance_date in enumerate(rebalances):
        next_cutoff = rebalances[idx + 1] if idx + 1 < len(rebalances) else price_pivot.index[-1]
        signal_slice = signals.loc[signals["as_of"] == rebalance_date]
        chosen = signal_slice.nlargest(config.top_k, "score")["ticker"].tolist()
        if not chosen:
            continue
        period_prices = price_pivot.loc[(price_pivot.index >= rebalance_date) & (price_pivot.index <= next_cutoff), chosen]
        if period_prices.empty:
            continue
        entry_prices = period_prices.iloc[0]
        exit_prices = period_prices.iloc[-1]
        gross_return = (exit_prices / entry_prices - 1).mean()
        cost = (config.cost_bps + config.slippage_bps) / 10000
        net_return = gross_return - cost
        equity *= (1 + net_return)
        equity_curve.append(equity)
        daily_returns.append(net_return)

        for ticker in chosen:
            series = period_prices[ticker]
            max_ret = float(series.max() / series.iloc[0] - 1)
            trades.append(
                {
                    "ticker": ticker,
                    "entry_date": period_prices.index[0],
                    "exit_date": period_prices.index[-1],
                    "entry_price": float(series.iloc[0]),
                    "exit_price": float(series.iloc[-1]),
                    "max_return": max_ret,
                }
            )

    metrics = {
        "CAGR": CAGR(equity_curve),
        "Sharpe": sharpe_ratio(daily_returns),
        "MaxDrawdown": max_drawdown(equity_curve),
        "HitRate": hit_rate(trades),
    }
    return BacktestResult(equity_curve=equity_curve or [1.0], metrics=metrics, trades=trades)


__all__ = ["BacktestConfig", "run_backtest"]
