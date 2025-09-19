"""Typed data contracts used across the project."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Literal, Optional, TypedDict


class SecurityId(TypedDict, total=False):
    """Canonical identifier for a security.

    The structure follows the specification outlined in the project brief.  Fields are
    optional to make it easy to construct identifiers gradually as more mapping data
    becomes available during ingestion.
    """

    ticker: str
    cik: Optional[str]
    sedar_issuer_id: Optional[str]
    cusip: Optional[str]
    country: Literal["US", "CA"]
    exchange: str
    currency: str


class InsiderBlock(TypedDict, total=False):
    net_buys_usd_30d: float
    cluster_count_30d: int
    unique_insiders_30d: int
    role_weighted_score: float
    after_drawdown: bool
    days_since_last_buy: Optional[int]


class WhaleBlock(TypedDict, total=False):
    has_13d_recent: bool
    g_percent_recent: Optional[float]
    qoq_13f_delta: Optional[float]
    consensus_new_positions: int
    fund_quality_score: float
    lag_penalty: float


class CatalystEvent(TypedDict, total=False):
    type: str
    date: str
    magnitude: Optional[float]
    source: str
    citation: Optional[str]


class QualityBlock(TypedDict, total=False):
    gm_trend_yr: float
    fcf_margin: Optional[float]
    dilution_yr: float
    r_and_d_to_sales: Optional[float]


class MomentumBlock(TypedDict, total=False):
    rs_3m: float
    dma_50_over_200: float
    time_since_52w_low: int


class RiskBlock(TypedDict, total=False):
    short_int_pct_float: Optional[float]
    borrow_fee: Optional[float]
    atm_recent: bool
    low_float_flag: bool


class ScoreBlock(TypedDict, total=False):
    insider: float
    whales: float
    catalysts: float
    quality: float
    momentum: float
    risk_penalty: float
    composite: float


class PITFeatures(TypedDict, total=False):
    as_of: date
    ticker: str
    mkt_cap_usd: float
    adtv_usd: float
    float_pct: Optional[float]

    insider: InsiderBlock
    whales: WhaleBlock
    catalysts: List[CatalystEvent]
    quality: QualityBlock
    momentum: MomentumBlock
    risk: RiskBlock

    scores: ScoreBlock
    explanation: str
    citations: List[str]


@dataclass(slots=True)
class BacktestResult:
    """Container for backtest outputs used by :mod:`tests.test_backtest`."""

    equity_curve: List[float]
    metrics: Dict[str, float]
    trades: List[Dict[str, object]]
