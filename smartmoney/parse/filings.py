"""Parsing helpers for 8-K/6-K/10-Q/10-K filings."""

from __future__ import annotations

import re
from typing import Iterable, List

import pandas as pd

from ..types import CatalystEvent

BUYBACK_RE = re.compile(r"buyback|repurchase", re.I)
CONTRACT_RE = re.compile(r"contract|agreement|loi", re.I)
GUIDANCE_RE = re.compile(r"guidance", re.I)
CLINICAL_RE = re.compile(r"phase [123]|trial", re.I)
EARNINGS_RE = re.compile(r"earnings call|results", re.I)


def extract_events_from_filings(docs: Iterable[dict]) -> List[CatalystEvent]:
    events: List[CatalystEvent] = []
    for doc in docs:
        text = doc.get("text", "")
        date = doc.get("filing_date")
        source = doc.get("source", "8-K")
        citation = doc.get("url")
        lowered = text.lower()
        if BUYBACK_RE.search(lowered):
            events.append({"type": "buyback", "date": date, "magnitude": doc.get("magnitude"), "source": source, "citation": citation})
        if CONTRACT_RE.search(lowered):
            events.append({"type": "contract", "date": date, "magnitude": doc.get("magnitude"), "source": source, "citation": citation})
        if GUIDANCE_RE.search(lowered):
            events.append({"type": "guidance", "date": date, "magnitude": doc.get("magnitude"), "source": source, "citation": citation})
        if CLINICAL_RE.search(lowered):
            events.append({"type": "clinical", "date": date, "magnitude": doc.get("magnitude"), "source": source, "citation": citation})
        if EARNINGS_RE.search(lowered):
            events.append({"type": "earnings", "date": date, "magnitude": doc.get("magnitude"), "source": source, "citation": citation})
    return events


def events_to_frame(events: List[CatalystEvent]) -> pd.DataFrame:
    return pd.DataFrame(events)


__all__ = ["extract_events_from_filings", "events_to_frame"]
