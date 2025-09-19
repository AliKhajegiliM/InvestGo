"""Catalyst detection and scoring."""

from __future__ import annotations

from typing import Iterable, List, Tuple

import pandas as pd

from ..types import CatalystEvent
from ..utils.dates import snap_asof

EVENT_WEIGHTS = {
    "earnings": 0.15,
    "buyback": 0.2,
    "contract": 0.2,
    "clinical": 0.25,
    "guidance": 0.15,
    "news": 0.1,
}


def _normalise_events(events: Iterable[CatalystEvent]) -> List[CatalystEvent]:
    out: List[CatalystEvent] = []
    for event in events:
        item = dict(event)
        if item.get("date"):
            item["date"] = pd.to_datetime(item["date"]).date().isoformat()
        out.append(item)  # type: ignore[arg-type]
    return out


def compute_catalyst_features(events: Iterable[CatalystEvent], as_of: str, window: int = 90) -> Tuple[float, List[CatalystEvent]]:
    as_of_date = snap_asof(as_of)
    events = _normalise_events(events)
    upcoming: List[CatalystEvent] = []
    score = 0.0
    for event in events:
        date_str = event.get("date")
        if not date_str:
            continue
        event_date = pd.to_datetime(date_str).date()
        delta = (event_date - as_of_date).days
        if -5 <= delta <= window:
            upcoming.append(event)
            weight = EVENT_WEIGHTS.get(event.get("type", "news"), 0.1)
            recency = max(0.0, (window - abs(delta)) / window)
            score += weight * (0.5 + 0.5 * recency)
    score = min(score, 1.0)
    return score, upcoming


__all__ = ["compute_catalyst_features", "EVENT_WEIGHTS"]
