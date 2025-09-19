"""Command line interface for the SmartMoney project."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Iterable, List

import pandas as pd

from smartmoney.features.catalysts import compute_catalyst_features
from smartmoney.features.insider import compute_insider_features
from smartmoney.features.momentum import compute_momentum_features
from smartmoney.features.quality import compute_quality_features
from smartmoney.features.risk import compute_risk_penalty
from smartmoney.features.whales import compute_whale_features
from smartmoney.scoring.composite import build_explanation, composite_score, DEFAULT_WEIGHTS
from smartmoney.ui.report import render_report, save_report
from smartmoney.utils.io import load_config, read_dataframe, write_dataframe
from smartmoney.backtest.simulator import BacktestConfig, run_backtest
from smartmoney.backtest.loaders import load_backtest_inputs
from smartmoney.utils.log import get_logger

LOGGER = get_logger(__name__)


def _load_optional(path: str | None) -> pd.DataFrame:
    if not path:
        return pd.DataFrame()
    file = Path(path)
    if not file.exists():
        raise FileNotFoundError(f"Input file {file} not found")
    return read_dataframe(file)


def cmd_ingest(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    LOGGER.info("Ingestion placeholder executed with config exchanges: %s", config.get("universe", {}).get("exchanges"))


def _collect_tickers(frames: Iterable[pd.DataFrame]) -> List[str]:
    tickers: set[str] = set()
    for frame in frames:
        if frame is not None and not frame.empty and "ticker" in frame.columns:
            tickers.update(frame["ticker"].dropna().astype(str).unique())
    return sorted(tickers)


def cmd_build_features(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    weights = config.get("scoring", {}).get("weights", DEFAULT_WEIGHTS)
    as_of = args.as_of

    insiders = _load_optional(args.insiders)
    whales = _load_optional(args.whales)
    thirteenf = _load_optional(args.thirteenf)
    catalysts_df = _load_optional(args.catalysts)
    financials = _load_optional(args.financials)
    prices = _load_optional(args.prices)
    risk_df = _load_optional(args.risk)

    tickers = _collect_tickers([insiders, whales, thirteenf, catalysts_df, financials, prices, risk_df])
    rows = []
    for ticker in tickers:
        insider_txn = insiders.loc[insiders["ticker"] == ticker] if not insiders.empty else pd.DataFrame()
        price_hist = prices.loc[prices["ticker"] == ticker] if not prices.empty else pd.DataFrame()
        insider_score, insider_block = compute_insider_features(insider_txn, as_of, price_hist)

        whale_events = whales.loc[whales["ticker"] == ticker] if not whales.empty else pd.DataFrame()
        f13_positions = thirteenf.loc[thirteenf["ticker"] == ticker] if not thirteenf.empty else pd.DataFrame()
        whale_score, whale_block = compute_whale_features(whale_events, f13_positions, as_of)

        cat_events = []
        if not catalysts_df.empty:
            cat_events = catalysts_df.loc[catalysts_df["ticker"] == ticker].to_dict(orient="records")
        catalyst_score, catalyst_block = compute_catalyst_features(cat_events, as_of)

        fin_rows = financials.loc[financials["ticker"] == ticker] if not financials.empty else pd.DataFrame()
        quality_score, quality_block = compute_quality_features(fin_rows, as_of)

        momentum_score, momentum_block = compute_momentum_features(price_hist, as_of)

        risk_row = risk_df.loc[risk_df["ticker"] == ticker].iloc[0].to_dict() if not risk_df.empty and ticker in risk_df["ticker"].values else {}
        risk_penalty, risk_block = compute_risk_penalty(risk_row)

        component_scores = {
            "insider": insider_score,
            "whales": whale_score,
            "catalysts": catalyst_score,
            "quality": quality_score,
            "momentum": momentum_score,
            "risk_penalty": risk_penalty,
        }
        composite = composite_score(component_scores, weights)
        scores = {**component_scores, "composite": composite}
        explanation = build_explanation(ticker, {"insider": insider_block, "whales": whale_block}, scores, catalyst_block, risk_block)
        row = {
            "as_of": as_of,
            "ticker": ticker,
            "mkt_cap_usd": price_hist["mkt_cap_usd"].iloc[-1] if "mkt_cap_usd" in price_hist.columns and not price_hist.empty else None,
            "adtv_usd": price_hist["adtv_usd"].iloc[-1] if "adtv_usd" in price_hist.columns and not price_hist.empty else None,
            "float_pct": None,
            "insider": insider_block,
            "whales": whale_block,
            "catalysts": catalyst_block,
            "quality": quality_block,
            "momentum": momentum_block,
            "risk": risk_block,
            "scores": scores,
            "explanation": explanation,
            "citations": [evt.get("citation") for evt in catalyst_block if evt.get("citation")],
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    out_path = write_dataframe(df, args.out)
    LOGGER.info("Features saved to %s", out_path)


def cmd_rank(args: argparse.Namespace) -> None:
    features = read_dataframe(args.features)
    if "scores.composite" in features.columns:
        features = features.rename(columns={"scores.composite": "composite"})
    if "composite" not in features.columns and "scores" in features.columns:
        features["composite"] = features["scores"].apply(lambda s: s.get("composite", 0))
    ranked = features.sort_values("composite", ascending=False)
    out = write_dataframe(ranked, args.out)
    LOGGER.info("Ranked watchlist written to %s", out)


def cmd_report(args: argparse.Namespace) -> None:
    features = read_dataframe(args.features)
    rows = features.to_dict(orient="records")
    content = render_report(rows, top_n=args.top, fmt=args.format)
    save_report(content, args.out)
    LOGGER.info("Report saved to %s", args.out)


def cmd_backtest(args: argparse.Namespace) -> None:
    prices, signals = load_backtest_inputs(args.prices, args.signals)
    config = BacktestConfig(rebalance_days=args.rebalance_days, top_k=args.top_k)
    result = run_backtest(prices, signals, config)
    LOGGER.info("Backtest metrics: %s", result.metrics)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SmartMoney nightly pipeline")
    parser.add_argument("--config", default=None, help="Path to YAML config")
    subparsers = parser.add_subparsers(dest="command")

    ingest = subparsers.add_parser("ingest", help="Download latest disclosures")
    ingest.set_defaults(func=cmd_ingest)

    features = subparsers.add_parser("build-features", help="Compute feature set")
    features.add_argument("--as-of", required=True)
    features.add_argument("--insiders")
    features.add_argument("--whales")
    features.add_argument("--thirteenf")
    features.add_argument("--catalysts")
    features.add_argument("--financials")
    features.add_argument("--prices")
    features.add_argument("--risk")
    features.add_argument("--out", required=True)
    features.set_defaults(func=cmd_build_features)

    rank = subparsers.add_parser("rank", help="Rank universe by composite score")
    rank.add_argument("--features", required=True)
    rank.add_argument("--out", required=True)
    rank.set_defaults(func=cmd_rank)

    report = subparsers.add_parser("report", help="Render HTML/Markdown report")
    report.add_argument("--features", required=True)
    report.add_argument("--top", type=int, default=30)
    report.add_argument("--format", choices=["html", "markdown"], default="html")
    report.add_argument("--out", required=True)
    report.set_defaults(func=cmd_report)

    backtest = subparsers.add_parser("backtest", help="Run historical simulation")
    backtest.add_argument("--prices", required=True)
    backtest.add_argument("--signals", required=True)
    backtest.add_argument("--rebalance-days", type=int, default=30)
    backtest.add_argument("--top-k", type=int, default=15)
    backtest.set_defaults(func=cmd_backtest)

    return parser


def main(argv: List[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return
    args.func(args)


if __name__ == "__main__":
    main()
