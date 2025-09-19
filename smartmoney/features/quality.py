"""Business quality scoring."""

from __future__ import annotations

from typing import Dict, Tuple

import pandas as pd


def _scale(value: float, lower: float, upper: float) -> float:
    if value is None:
        return 0.5
    if upper == lower:
        return 0.5
    score = (value - lower) / (upper - lower)
    return max(0.0, min(1.0, score))


def compute_quality_features(financials: pd.DataFrame, as_of: str, industry_medians: Dict[str, float] | None = None) -> Tuple[float, dict]:
    if financials is None or financials.empty:
        block = {"gm_trend_yr": 0.0, "fcf_margin": None, "dilution_yr": 0.0, "r_and_d_to_sales": None}
        return 0.0, block

    financials = financials.sort_values("period")
    gm_trend = 0.0
    if "gross_margin" in financials.columns and len(financials) >= 2:
        gm_trend = float(financials.iloc[-1]["gross_margin"] - financials.iloc[-2]["gross_margin"])
    fcf_margin = float(financials.iloc[-1].get("fcf_margin", 0.0)) if "fcf_margin" in financials.columns else None
    dilution = 0.0
    if "shares_outstanding" in financials.columns and len(financials) >= 2:
        prev = float(financials.iloc[-2]["shares_outstanding"] or 0)
        last = float(financials.iloc[-1]["shares_outstanding"] or 0)
        if prev > 0:
            dilution = (last - prev) / prev
    r_and_d_to_sales = None
    if {"r_and_d", "sales"}.issubset(financials.columns):
        sales = float(financials.iloc[-1]["sales"] or 0)
        if sales > 0:
            r_and_d_to_sales = float(financials.iloc[-1]["r_and_d"]) / sales

    score = 0.0
    score += 0.3 * _scale(gm_trend, -0.2, 0.2)
    if fcf_margin is not None:
        score += 0.3 * _scale(fcf_margin, -0.1, 0.2)
    score += 0.25 * _scale(-dilution, -0.2, 0.1)
    if r_and_d_to_sales is not None:
        score += 0.15 * _scale(0.3 - r_and_d_to_sales, 0.0, 0.3)
    score = min(1.0, max(0.0, score))

    block = {
        "gm_trend_yr": gm_trend,
        "fcf_margin": fcf_margin,
        "dilution_yr": dilution,
        "r_and_d_to_sales": r_and_d_to_sales,
    }
    return score, block


__all__ = ["compute_quality_features"]
