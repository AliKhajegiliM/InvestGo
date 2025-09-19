"""Composite scoring for the SmartMoney watchlist."""

from __future__ import annotations

from typing import Dict, List, Tuple

from ..types import CatalystEvent

DEFAULT_WEIGHTS = {
    "insider": 0.25,
    "whales": 0.25,
    "catalysts": 0.2,
    "quality": 0.15,
    "momentum": 0.1,
    "risk_penalty": 0.15,
}


def composite_score(component_scores: Dict[str, float], weights: Dict[str, float] | None = None) -> float:
    weights = weights or DEFAULT_WEIGHTS
    total_positive = weights.get("insider", 0) + weights.get("whales", 0) + weights.get("catalysts", 0) + weights.get("quality", 0) + weights.get("momentum", 0)
    raw = (
        component_scores.get("insider", 0) * weights.get("insider", 0)
        + component_scores.get("whales", 0) * weights.get("whales", 0)
        + component_scores.get("catalysts", 0) * weights.get("catalysts", 0)
        + component_scores.get("quality", 0) * weights.get("quality", 0)
        + component_scores.get("momentum", 0) * weights.get("momentum", 0)
    )
    raw -= component_scores.get("risk_penalty", 0) * weights.get("risk_penalty", 0)
    if total_positive <= 0:
        return 0.0
    score = raw / total_positive
    return max(0.0, min(1.0, score))


def build_explanation(ticker: str, features: Dict[str, dict], scores: Dict[str, float], catalysts: List[CatalystEvent], risk: Dict[str, float | bool | None]) -> str:
    bullets: List[str] = []
    insider = features.get("insider", {})
    if scores.get("insider", 0) > 0 and insider:
        bullets.append(
            f"+ Insider cluster: {insider.get('unique_insiders_30d', 0)} insiders bought ${insider.get('net_buys_usd_30d', 0):,.0f} in last 30d"
        )
    whales = features.get("whales", {})
    if scores.get("whales", 0) > 0 and whales:
        parts = []
        if whales.get("has_13d_recent"):
            parts.append("new 13D")
        if whales.get("qoq_13f_delta"):
            parts.append(f"13F delta {whales['qoq_13f_delta']:.1%}")
        bullets.append("+ Whales: " + ", ".join(parts) if parts else "+ Whales: accumulation signals")
    if catalysts:
        cat_types = sorted({c.get("type", "event") for c in catalysts})
        bullets.append("+ Catalysts: " + ", ".join(cat_types))
    if risk:
        risk_bits = []
        if (risk.get("short_int_pct_float") or 0) > 15:
            risk_bits.append(f"short {risk['short_int_pct_float']:.1f}% float")
        if (risk.get("borrow_fee") or 0) > 10:
            risk_bits.append(f"borrow {risk['borrow_fee']:.1f}%")
        if risk.get("atm_recent"):
            risk_bits.append("ATM filed")
        if risk.get("low_float_flag"):
            risk_bits.append("low float")
        if risk_bits:
            bullets.append("- Risk: " + ", ".join(risk_bits))
    return "; ".join(bullets) if bullets else f"{ticker} has limited datapoints"


__all__ = ["composite_score", "build_explanation", "DEFAULT_WEIGHTS"]
