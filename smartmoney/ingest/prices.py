"""Price loader with a pluggable data provider interface."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Optional

import pandas as pd

from ..utils.io import ensure_dir

try:  # pragma: no cover - optional dependency
    import yfinance as yf  # type: ignore
except Exception:  # pragma: no cover
    yf = None


@dataclass(slots=True)
class PriceSettings:
    provider: str = "yfinance"
    cache_dir: Path = Path("./data/prices")


class PriceClient:
    def __init__(self, settings: PriceSettings):
        self.settings = settings
        ensure_dir(settings.cache_dir)

    def fetch(self, ticker: str, start: date, end: date, data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        if data is not None:
            return self._normalize(data)
        if self.settings.provider == "yfinance" and yf is not None:
            df = yf.download(ticker, start=start, end=end, auto_adjust=False, progress=False)
            df.index = pd.to_datetime(df.index)
            df = df.rename(columns=str.lower)
            df["ticker"] = ticker
            df = df.reset_index().rename(columns={"index": "date"})
            return self._normalize(df)
        raise RuntimeError("No price provider available; pass `data` explicitly in tests")

    def _normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        columns = {c.lower(): c for c in df.columns}
        date_col = "date" if "date" in columns else df.columns[0]
        out = df.copy()
        out["date"] = pd.to_datetime(out[date_col]).dt.date
        out = out.rename(columns={columns.get("close", "close"): "close", columns.get("volume", "volume"): "volume"})
        for col in ("adj_close", "open", "high", "low"):
            if col in columns:
                out[col] = df[columns[col]]
        if "ticker" not in out.columns:
            out["ticker"] = df.get("ticker", "UNKNOWN")
        return out[["ticker", "date", "close", "volume"] + [c for c in ["open", "high", "low", "adj_close"] if c in out.columns]]


def compute_liquidity_metrics(prices: pd.DataFrame, shares_outstanding: float | None = None, close_column: str = "close") -> pd.DataFrame:
    df = prices.copy()
    df = df.sort_values(["ticker", "date"]).reset_index(drop=True)
    df["adtv_usd"] = df.groupby("ticker")["volume"].transform(lambda s: s.rolling(window=20, min_periods=1).mean()) * df[close_column]
    if shares_outstanding is not None:
        df["mkt_cap_usd"] = shares_outstanding * df[close_column]
    return df


__all__ = ["PriceSettings", "PriceClient", "compute_liquidity_metrics"]
