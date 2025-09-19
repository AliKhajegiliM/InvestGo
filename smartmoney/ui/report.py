"""Watchlist reporting helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from ..types import PITFeatures


def build_report_table(rows: Iterable[PITFeatures]) -> pd.DataFrame:
    records = []
    for row in rows:
        records.append(
            {
                "Ticker": row.get("ticker"),
                "Market Cap (USD)": row.get("mkt_cap_usd"),
                "ADTV (USD)": row.get("adtv_usd"),
                "Composite": row.get("scores", {}).get("composite"),
                "Insider": row.get("scores", {}).get("insider"),
                "Whales": row.get("scores", {}).get("whales"),
                "Catalysts": row.get("scores", {}).get("catalysts"),
                "Quality": row.get("scores", {}).get("quality"),
                "Momentum": row.get("scores", {}).get("momentum"),
                "Risk": row.get("scores", {}).get("risk_penalty"),
                "Explanation": row.get("explanation"),
            }
        )
    return pd.DataFrame(records)


def render_report(rows: Iterable[PITFeatures], top_n: int = 30, fmt: str = "html") -> str:
    table = build_report_table(rows).sort_values("Composite", ascending=False).head(top_n)
    if fmt == "markdown":
        return table.to_markdown(index=False)
    return table.to_html(index=False, escape=False)


def save_report(content: str, path: str | Path) -> Path:
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content, encoding="utf-8")
    return dest


__all__ = ["render_report", "save_report", "build_report_table"]
