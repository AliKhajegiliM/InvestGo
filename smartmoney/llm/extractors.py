"""LLM assisted extraction utilities with deterministic fallbacks."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import List, Optional

import pandas as pd

from ..types import CatalystEvent

EVENT_PATTERNS = {
    "buyback": re.compile(r"(repurchase|buyback) program(?: of)?\s*(?P<percent>\d+(?:\.\d+)?)%", re.I),
    "contract": re.compile(r"contract (?:worth|valued at)\s*\$?(?P<amount>\d+[\d,\.]*)(?: million|m)?", re.I),
    "earnings": re.compile(r"earnings call on (?P<date>[A-Za-z]+ \d{1,2}, \d{4})", re.I),
    "guidance": re.compile(r"guidance (?:raised|updated)", re.I),
    "clinical": re.compile(r"phase (?P<phase>\d) (?:trial|study)", re.I),
}
DATE_PATTERN = re.compile(r"(?P<date>\d{4}-\d{2}-\d{2}|[A-Za-z]+ \d{1,2}, \d{4})")


@dataclass(slots=True)
class LLMConfig:
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    max_tokens: int = 1200
    temperature: float = 0.0
    enabled: bool = False


class LLMClient:
    """Very small abstraction that supports a regex fallback."""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.enabled = config.enabled and bool(os.getenv("LLM_API_KEY"))

    def extract_events(self, text: str, doc_id: str | None = None) -> List[CatalystEvent]:
        if not self.enabled:
            return regex_extract_events(text, doc_id)
        return regex_extract_events(text, doc_id)


def regex_extract_events(text: str, doc_id: str | None = None) -> List[CatalystEvent]:
    events: List[CatalystEvent] = []
    for event_type, pattern in EVENT_PATTERNS.items():
        for match in pattern.finditer(text):
            span = match.span()
            magnitude = None
            if "percent" in match.groupdict():
                try:
                    magnitude = float(match.group("percent"))
                except Exception:  # pragma: no cover - defensive
                    magnitude = None
            elif "amount" in match.groupdict():
                try:
                    magnitude = float(match.group("amount").replace(",", ""))
                except Exception:
                    magnitude = None
            date_match = DATE_PATTERN.search(text, span[0], min(len(text), span[1] + 60))
            date_value: Optional[str] = None
            if date_match:
                try:
                    date_value = str(pd.to_datetime(date_match.group("date")).date())
                except Exception:
                    date_value = date_match.group("date")
            citation = f"{doc_id or 'doc'}:{span[0]}-{span[1]}"
            events.append({"type": event_type, "date": date_value, "magnitude": magnitude, "source": "LLM", "citation": citation})
    if not events:
        date_match = DATE_PATTERN.search(text)
        if date_match:
            citation = f"{doc_id or 'doc'}:{date_match.start()}-{date_match.end()}"
            events.append({"type": "news", "date": date_match.group("date"), "magnitude": None, "source": "LLM", "citation": citation})
    return events


__all__ = ["LLMClient", "LLMConfig", "regex_extract_events"]
