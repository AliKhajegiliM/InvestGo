"""Simple news normaliser used for catalyst detection."""

from __future__ import annotations

from typing import Iterable, List

import pandas as pd

from ..types import CatalystEvent


def normalise_news(records: Iterable[dict]) -> pd.DataFrame:
    rows: List[dict] = []
    for record in records:
        rows.append(
            {
                "ticker": record.get("ticker"),
                "headline": record.get("headline"),
                "published": record.get("published"),
                "source": record.get("source", "News"),
                "url": record.get("url"),
                "category": record.get("category"),
            }
        )
    return pd.DataFrame(rows)


def to_catalyst_events(df: pd.DataFrame) -> List[CatalystEvent]:
    events: List[CatalystEvent] = []
    for _, row in df.iterrows():
        events.append(
            {
                "type": row.get("category") or "news",
                "date": row.get("published"),
                "magnitude": None,
                "source": row.get("source", "News"),
                "citation": row.get("url"),
            }
        )
    return events


__all__ = ["normalise_news", "to_catalyst_events"]
