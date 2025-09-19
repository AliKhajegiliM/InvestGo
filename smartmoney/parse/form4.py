"""Parser for SEC Form 4 filings."""

from __future__ import annotations

from typing import List

import pandas as pd

OPEN_MARKET_CODES = {"P"}
ROLE_ALIASES = {
    "chief executive officer": "CEO",
    "ceo": "CEO",
    "chief financial officer": "CFO",
    "cfo": "CFO",
    "chief operating officer": "COO",
    "coo": "COO",
}


def _normalise_role(relationship: dict) -> str:
    officer_title = (relationship or {}).get("officerTitle")
    if officer_title:
        key = officer_title.strip().lower()
        for alias, role in ROLE_ALIASES.items():
            if alias in key:
                return role
    if (relationship or {}).get("director") in {"true", True}:
        return "Director"
    return "Other"


def parse_form4_transactions(form4_json: dict) -> pd.DataFrame:
    issuer = form4_json.get("issuerTradingSymbol") or form4_json.get("issuer", {}).get("issuerTradingSymbol")
    owners = form4_json.get("reportingOwners", [])
    transactions = form4_json.get("nonDerivativeTable", {}).get("nonDerivativeTransaction", [])
    if isinstance(transactions, dict):
        transactions = [transactions]

    rows: List[dict] = []
    for txn in transactions:
        code = (txn.get("transactionCoding") or {}).get("transactionCode")
        if code not in OPEN_MARKET_CODES:
            continue
        amounts = txn.get("transactionAmounts", {})
        shares = float((amounts.get("transactionShares") or {}).get("value", 0))
        price = float((amounts.get("transactionPricePerShare") or {}).get("value", 0))
        value = shares * price
        trade_date = (txn.get("transactionDate") or {}).get("value")
        for owner in owners:
            relationship = owner.get("reportingOwnerRelationship", {})
            name_obj = owner.get("reportingOwner", {})
            insider_name = name_obj.get("rptOwnerName") or name_obj.get("reportingOwnerName")
            rows.append(
                {
                    "ticker": issuer,
                    "trade_date": trade_date,
                    "shares": shares,
                    "price": price,
                    "transaction_value": value,
                    "insider_role": _normalise_role(relationship),
                    "insider_name": insider_name,
                }
            )
    return pd.DataFrame(rows)


def aggregate_form4_purchases(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    grouped = (
        df.groupby(["ticker", "trade_date", "insider_role"], as_index=False)["transaction_value"].sum().rename(columns={"transaction_value": "value_usd"})
    )
    return grouped


__all__ = ["parse_form4_transactions", "aggregate_form4_purchases"]
