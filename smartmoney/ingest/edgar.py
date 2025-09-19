"""Lightweight EDGAR client used by the nightly pipeline."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd
import requests

from ..utils.io import ensure_dir, load_config
from ..utils.log import get_logger
from ..utils.ptit import ensure_sorted
from ..parse.form4 import parse_form4_transactions
from ..parse.form13 import parse_13d_g, parse_13f_holdings

LOGGER = get_logger(__name__)


@dataclass(slots=True)
class EdgarSettings:
    base_url: str
    user_agent: str
    cache_dir: Path


class EdgarClient:
    """Small helper around the SEC data API."""

    def __init__(self, settings: EdgarSettings):
        self.settings = settings
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": settings.user_agent})
        ensure_dir(settings.cache_dir)

    def _build_url(self, path: str) -> str:
        base = self.settings.base_url.rstrip("/")
        if base.startswith("http"):
            return f"{base}/{path.lstrip('/')}"
        return str(Path(base) / path)

    def get_json(self, path: str) -> dict:
        url = self._build_url(path)
        if url.startswith("http"):
            LOGGER.debug("Requesting %s", url)
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        return json.loads(Path(url).read_text(encoding="utf-8"))

    def get_text(self, path: str) -> str:
        url = self._build_url(path)
        if url.startswith("http"):
            LOGGER.debug("Requesting %s", url)
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        return Path(url).read_text(encoding="utf-8")

    def load_form4(self, records: Iterable[dict]) -> pd.DataFrame:
        frames = [parse_form4_transactions(record) for record in records]
        if not frames:
            return pd.DataFrame(columns=["ticker", "trade_date", "shares", "price", "transaction_value", "insider_role"])
        return ensure_sorted(pd.concat(frames, ignore_index=True), by="trade_date")

    def load_13d_g(self, texts: Iterable[str], ticker: str) -> pd.DataFrame:
        rows = []
        for text in texts:
            rows.extend(parse_13d_g(text, ticker))
        return ensure_sorted(pd.DataFrame(rows), by="filing_date") if rows else pd.DataFrame(columns=["ticker", "filer", "percent", "filing_date", "form_type"])

    def load_13f(self, text: str, cik_to_ticker: Optional[dict] = None) -> pd.DataFrame:
        cik_map = cik_to_ticker or {}
        data = parse_13f_holdings(text, cik_map)
        return ensure_sorted(pd.DataFrame(data), by="filing_date")


def build_client(config_path: Optional[str | Path] = None, cache_subdir: str = "sec") -> EdgarClient:
    config = load_config(config_path)
    sec_cfg = config.get("data", {}).get("sec", {})
    cache_dir = Path(config.get("data", {}).get("cache_dir", "./data")).resolve() / cache_subdir
    settings = EdgarSettings(
        base_url=sec_cfg.get("base_url", "https://data.sec.gov"),
        user_agent=sec_cfg.get("user_agent", "smartmoney/0.1"),
        cache_dir=cache_dir,
    )
    return EdgarClient(settings)


__all__ = ["EdgarSettings", "EdgarClient", "build_client"]
