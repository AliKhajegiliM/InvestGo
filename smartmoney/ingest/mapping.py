"""Ticker/identifier mapping utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

import pandas as pd

from ..types import SecurityId


@dataclass
class MappingTable:
    records: Dict[str, SecurityId] = field(default_factory=dict)

    def upsert(self, record: SecurityId) -> None:
        ticker = record["ticker"].upper()
        existing = self.records.get(ticker, {})
        merged = {**existing, **record}
        merged["ticker"] = ticker
        self.records[ticker] = merged  # type: ignore[assignment]

    def get(self, ticker: str) -> Optional[SecurityId]:
        return self.records.get(ticker.upper())

    def to_frame(self) -> pd.DataFrame:
        if not self.records:
            return pd.DataFrame(columns=["ticker", "cik", "sedar_issuer_id", "cusip", "country", "exchange", "currency"])
        return pd.DataFrame(list(self.records.values()))

    @classmethod
    def from_frame(cls, df: pd.DataFrame) -> "MappingTable":
        table = cls()
        for _, row in df.iterrows():
            record: SecurityId = {
                "ticker": row.get("ticker"),
                "cik": row.get("cik"),
                "sedar_issuer_id": row.get("sedar_issuer_id"),
                "cusip": row.get("cusip"),
                "country": row.get("country", "US"),
                "exchange": row.get("exchange", "UNKNOWN"),
                "currency": row.get("currency", "USD"),
            }
            table.upsert(record)
        return table


__all__ = ["MappingTable"]
