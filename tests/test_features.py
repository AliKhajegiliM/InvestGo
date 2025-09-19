from __future__ import annotations

import pandas as pd

from smartmoney.features.catalysts import compute_catalyst_features
from smartmoney.features.insider import compute_insider_features
from smartmoney.features.whales import lag_penalty


def test_insider_cluster_detection_counts_unique():
    transactions = pd.DataFrame(
        [
            {"ticker": "XYZ", "trade_date": "2024-02-01", "transaction_value": 25000, "insider_role": "CEO", "insider_name": "A"},
            {"ticker": "XYZ", "trade_date": "2024-02-05", "transaction_value": 30000, "insider_role": "CFO", "insider_name": "B"},
        ]
    )
    score, block = compute_insider_features(transactions, "2024-02-20")
    assert block["cluster_count_30d"] >= 1
    assert block["unique_insiders_30d"] == 2
    assert score > 0


def test_lag_penalty_piecewise_decay():
    assert lag_penalty(0) == 1.0
    assert lag_penalty(90) <= 0.3
    assert lag_penalty(200) == 0.0


def test_catalyst_scoring_increases_with_events():
    events = [
        {"type": "earnings", "date": "2024-03-15", "magnitude": None, "source": "News"},
        {"type": "buyback", "date": "2024-03-20", "magnitude": 5.0, "source": "8-K"},
    ]
    score, upcoming = compute_catalyst_features(events, "2024-03-01")
    single_score, _ = compute_catalyst_features(events[:1], "2024-03-01")
    assert score > single_score
    assert len(upcoming) == 2
