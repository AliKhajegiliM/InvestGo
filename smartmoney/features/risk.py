"""Risk penalty features."""

from __future__ import annotations

from typing import Dict, Tuple


def compute_risk_penalty(risk_inputs: Dict[str, float | bool | None]) -> Tuple[float, Dict[str, float | bool | None]]:
    short_interest = float(risk_inputs.get("short_int_pct_float") or 0.0)
    borrow_fee = float(risk_inputs.get("borrow_fee") or 0.0)
    atm_recent = bool(risk_inputs.get("atm_recent", False))
    low_float_flag = bool(risk_inputs.get("low_float_flag", False))

    penalty = 0.0
    if short_interest > 15:
        penalty += 0.15 + min(0.1, (short_interest - 15) / 100)
    if borrow_fee > 10:
        penalty += 0.1 + min(0.1, (borrow_fee - 10) / 100)
    if atm_recent:
        penalty += 0.1
    if low_float_flag:
        penalty += 0.05

    penalty = min(0.4, penalty)
    block = {
        "short_int_pct_float": short_interest,
        "borrow_fee": borrow_fee,
        "atm_recent": atm_recent,
        "low_float_flag": low_float_flag,
    }
    return penalty, block


__all__ = ["compute_risk_penalty"]
