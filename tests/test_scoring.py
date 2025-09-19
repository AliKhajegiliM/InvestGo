from __future__ import annotations

from smartmoney.scoring.composite import composite_score


def test_composite_score_bounded_between_zero_and_one():
    components = {"insider": 0.9, "whales": 0.8, "catalysts": 0.7, "quality": 0.6, "momentum": 0.5, "risk_penalty": 0.1}
    score = composite_score(components)
    assert 0.0 <= score <= 1.0


def test_risk_penalty_reduces_composite():
    base = {"insider": 0.5, "whales": 0.5, "catalysts": 0.5, "quality": 0.5, "momentum": 0.5, "risk_penalty": 0.0}
    better = composite_score(base)
    base["risk_penalty"] = 0.3
    worse = composite_score(base)
    assert worse < better
