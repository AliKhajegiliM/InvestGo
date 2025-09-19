"""Helpers for Canadian SEDAR+/SEDI data."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

from ..utils.io import ensure_dir
from ..utils.ptit import ensure_sorted


@dataclass(slots=True)
class CanadaSettings:
    cache_dir: Path
    enable_sedi: bool = True


class CanadaClient:
    def __init__(self, settings: CanadaSettings):
        self.settings = settings
        ensure_dir(settings.cache_dir)

    def load_sedi(self, records: Iterable[dict]) -> pd.DataFrame:
        rows = []
        for record in records:
            rows.append(
                {
                    "issuer": record.get("issuer"),
                    "ticker": record.get("ticker"),
                    "trade_date": record.get("transactionDate"),
                    "shares": float(record.get("shares", 0.0)),
                    "price": float(record.get("price", 0.0)),
                    "transaction_value": float(record.get("value", 0.0)),
                    "insider_role": record.get("role", "Other"),
                }
            )
        if not rows:
            return pd.DataFrame(columns=["issuer", "ticker", "trade_date", "shares", "price", "transaction_value", "insider_role"])
        return ensure_sorted(pd.DataFrame(rows), by="trade_date")

    def load_early_warning(self, records: Iterable[dict]) -> pd.DataFrame:
        rows = []
        for record in records:
            rows.append(
                {
                    "ticker": record.get("ticker"),
                    "filer": record.get("filer"),
                    "percent": float(record.get("percent", 0.0)),
                    "filing_date": record.get("filing_date"),
                    "form_type": "EarlyWarning",
                }
            )
        if not rows:
            return pd.DataFrame(columns=["ticker", "filer", "percent", "filing_date", "form_type"])
        return ensure_sorted(pd.DataFrame(rows), by="filing_date")


__all__ = ["CanadaSettings", "CanadaClient"]
