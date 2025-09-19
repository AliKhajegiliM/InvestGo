from __future__ import annotations

import pandas as pd

from smartmoney.ingest.mapping import MappingTable
from smartmoney.ingest.prices import compute_liquidity_metrics


def test_mapping_round_trip_preserves_case_insensitivity():
    table = MappingTable()
    table.upsert({"ticker": "abc", "cik": "0001", "exchange": "NYSE", "currency": "USD", "country": "US"})
    table.upsert({"ticker": "ABC", "cusip": "123456789"})
    frame = table.to_frame()
    restored = MappingTable.from_frame(frame)
    record = restored.get("abc")
    assert record["cusip"] == "123456789"
    assert record["cik"] == "0001"


def test_compute_liquidity_metrics_derives_adtv_and_market_cap():
    prices = pd.DataFrame(
        [
            {"ticker": "XYZ", "date": "2024-01-01", "close": 10, "volume": 1000},
            {"ticker": "XYZ", "date": "2024-01-02", "close": 11, "volume": 1500},
            {"ticker": "XYZ", "date": "2024-01-03", "close": 12, "volume": 2000},
        ]
    )
    result = compute_liquidity_metrics(prices, shares_outstanding=1_000_000)
    assert "adtv_usd" in result.columns
    assert result.iloc[-1]["mkt_cap_usd"] == 12 * 1_000_000
