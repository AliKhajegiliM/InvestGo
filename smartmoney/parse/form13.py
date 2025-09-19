"""Parsers for Schedule 13D/G and 13F filings."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Dict, List

import pandas as pd

PERCENT_RE = re.compile(r"(?P<value>\d{1,2}(?:\.\d+)?)\s*%", re.I)
DATE_RE = re.compile(r"filed(?: on|:)\s*(?P<date>[A-Za-z0-9,\- ]{6,})", re.I)
REPORTER_RE = re.compile(r"name of reporting person[s]?:\s*(?P<name>.+)", re.I)
FORM_RE = re.compile(r"13[DG]", re.I)


def parse_13d_g(text: str, ticker: str) -> List[dict]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    joined = " \n".join(lines)
    form_match = FORM_RE.search(joined)
    form_type = "13G"
    if form_match:
        token = form_match.group(0).upper()
        form_type = token if token in {"13D", "13G"} else "13G"
    percent = None
    percent_match = PERCENT_RE.search(joined)
    if percent_match:
        percent = float(percent_match.group("value"))
    date_match = DATE_RE.search(joined)
    filing_date = None
    if date_match:
        try:
            filing_date = pd.to_datetime(date_match.group("date")).date().isoformat()
        except ValueError:
            filing_date = None
    reporter_match = REPORTER_RE.search(joined)
    filer = reporter_match.group("name").strip() if reporter_match else "Unknown Filer"

    return [
        {
            "ticker": ticker,
            "filer": filer,
            "percent": percent,
            "filing_date": filing_date,
            "form_type": form_type,
        }
    ]


def parse_13f_holdings(text: str, cik_to_ticker: Dict[str, str]) -> List[dict]:
    root = ET.fromstring(text)
    filing_date = None
    cik = None
    filer_name = None
    header = root.find(".//headerData")
    if header is not None:
        filing_date_elem = header.find("filingDate")
        if filing_date_elem is not None:
            filing_date = filing_date_elem.text
        cik_elem = header.find("filerInfo/filer")
        if cik_elem is not None:
            cik = cik_elem.findtext("credentials/cik")
            filer_name = cik_elem.findtext("name")
    info_tables = root.findall(".//infoTable")
    rows: List[dict] = []
    for table in info_tables:
        cusip = table.findtext("cusip")
        value = table.findtext("value")
        shares = table.findtext("shrsOrPrnAmt/sshPrnamt")
        ticker = table.findtext("nameOfIssuer")
        if cusip and cusip in cik_to_ticker:
            ticker = cik_to_ticker[cusip]
        rows.append(
            {
                "ticker": ticker,
                "cusip": cusip,
                "value": float(value) * 1000 if value else None,
                "shares": float(shares) if shares else None,
                "filing_date": filing_date,
                "filer_cik": cik,
                "filer_name": filer_name,
            }
        )
    return rows


__all__ = ["parse_13d_g", "parse_13f_holdings"]
