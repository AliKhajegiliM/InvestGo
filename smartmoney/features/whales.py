"""Institutional / whale accumulation features."""

from __future__ import annotations

from typing import Dict, List, Tuple

import pandas as pd

from ..utils.dates import snap_asof

_KNOTS = [(0, 1.0), (45, 0.6), (90, 0.3), (135, 0.15), (180, 0.0)]


def lag_penalty(days_since_filing: int) -> float:
    days = max(0, days_since_filing)
    for (d1, v1), (d2, v2) in zip(_KNOTS, _KNOTS[1:]):
        if days <= d2:
            if d2 == d1:
                return v2
            ratio = (days - d1) / (d2 - d1)
            return v1 + ratio * (v2 - v1)
    return 0.0


def _prepare(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if not out.empty:
        out["filing_date"] = pd.to_datetime(out["filing_date"])
    return out


def compute_whale_features(
    ownership_events: pd.DataFrame,
    f13_positions: pd.DataFrame,
    as_of: str,
    fund_quality: Dict[str, float] | None = None,
) -> Tuple[float, dict]:
    as_of_date = pd.Timestamp(snap_asof(as_of))
    ownership_events = _prepare(ownership_events)
    f13_positions = _prepare(f13_positions)

    has_13d_recent = False
    g_percent_recent = None
    if not ownership_events.empty:
        ownership_events["days_since"] = (as_of_date - ownership_events["filing_date"]).dt.days
        recent = ownership_events.loc[ownership_events["days_since"] <= 120]
        has_13d_recent = (recent["form_type"].str.upper() == "13D").any()
        g_recent = ownership_events.loc[(ownership_events["form_type"].str.upper() == "13G") & (ownership_events["days_since"] <= 365)]
        if not g_recent.empty and g_recent["percent"].notna().any():
            g_percent_recent = float(g_recent["percent"].max())

    quality_lookup = fund_quality or {}
    consensus_new_positions = 0
    fund_scores: List[float] = []
    qoq_deltas: List[float] = []
    lag_penalties: List[float] = []

    if not f13_positions.empty:
        grouping = f13_positions.groupby("filer_name") if "filer_name" in f13_positions.columns else [(None, f13_positions)]
        for filer, group in grouping:
            group = group.sort_values("filing_date")
            if group.empty:
                continue
            last = group.iloc[-1]
            days_since = int((as_of_date - pd.Timestamp(last["filing_date"])).days) if pd.notna(last.get("filing_date")) else 999
            lag_penalties.append(lag_penalty(days_since))
            fund_scores.append(quality_lookup.get(str(filer), 0.5))
            if len(group) >= 2:
                prev = group.iloc[-2]
                last_shares = float(last.get("shares") or 0)
                prev_shares = float(prev.get("shares") or 0)
                if prev_shares == 0 and last_shares > 0:
                    consensus_new_positions += 1
                    qoq_deltas.append(1.0)
                elif prev_shares > 0:
                    qoq_deltas.append((last_shares - prev_shares) / prev_shares)
            elif float(group.iloc[-1].get("shares") or 0) > 0:
                consensus_new_positions += 1
                qoq_deltas.append(1.0)

    avg_delta = float(pd.Series(qoq_deltas).mean()) if qoq_deltas else 0.0
    avg_fund_score = float(pd.Series(fund_scores).mean()) if fund_scores else 0.0
    avg_lag = float(pd.Series(lag_penalties).mean()) if lag_penalties else 1.0

    score = 0.0
    if has_13d_recent:
        score += 0.4
    if g_percent_recent:
        score += min(0.2, g_percent_recent / 50)
    score += min(0.25, max(0.0, avg_delta) * 0.5)
    score += min(0.15, avg_fund_score * 0.15)
    score *= avg_lag
    score = min(score, 1.0)

    block = {
        "has_13d_recent": has_13d_recent,
        "g_percent_recent": g_percent_recent,
        "qoq_13f_delta": avg_delta if qoq_deltas else None,
        "consensus_new_positions": consensus_new_positions,
        "fund_quality_score": avg_fund_score,
        "lag_penalty": avg_lag,
    }
    return score, block


__all__ = ["compute_whale_features", "lag_penalty"]
