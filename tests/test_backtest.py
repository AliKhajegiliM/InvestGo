from __future__ import annotations

import pandas as pd
import pytest

from smartmoney.backtest.simulator import BacktestConfig, run_backtest


def test_backtest_runs_on_toy_dataset():
    prices = pd.DataFrame(
        [
            {"date": "2024-01-01", "ticker": "AAA", "close": 10.0},
            {"date": "2024-01-02", "ticker": "AAA", "close": 11.0},
            {"date": "2024-01-03", "ticker": "AAA", "close": 12.0},
            {"date": "2024-01-04", "ticker": "AAA", "close": 12.0},
            {"date": "2024-01-01", "ticker": "BBB", "close": 8.0},
            {"date": "2024-01-02", "ticker": "BBB", "close": 8.0},
            {"date": "2024-01-03", "ticker": "BBB", "close": 9.0},
            {"date": "2024-01-04", "ticker": "BBB", "close": 9.9},
            {"date": "2024-01-01", "ticker": "CCC", "close": 5.0},
            {"date": "2024-01-02", "ticker": "CCC", "close": 5.5},
            {"date": "2024-01-03", "ticker": "CCC", "close": 5.5},
            {"date": "2024-01-04", "ticker": "CCC", "close": 6.0},
        ]
    )

    signals = pd.DataFrame(
        [
            {"as_of": "2024-01-01", "ticker": "AAA", "score": 0.9},
            {"as_of": "2024-01-01", "ticker": "BBB", "score": 0.7},
            {"as_of": "2024-01-01", "ticker": "CCC", "score": 0.3},
            {"as_of": "2024-01-03", "ticker": "BBB", "score": 0.7},
            {"as_of": "2024-01-03", "ticker": "CCC", "score": 0.9},
            {"as_of": "2024-01-03", "ticker": "AAA", "score": 0.2},
        ]
    )

    result = run_backtest(prices, signals, BacktestConfig(top_k=2))
    assert result.equity_curve[-1] == pytest.approx(1.2689, rel=1e-3)
    assert "CAGR" in result.metrics
    assert len(result.trades) == 4
