# SmartMoney Nightly Pipeline

This repository implements a research pipeline that ranks small and mid-cap US/Canadian equities by asymmetric upside.  The project provides data ingestion helpers, feature engineering blocks, composite scoring logic, a simple backtester and a CLI that stitches the pieces together into a nightly workflow.

## Project layout

```
smartmoney/
  config/settings.example.yaml    # sample configuration
  data/                           # local cache directory (ignored)
  smartmoney/                     # Python package
    ingest/                       # SEC/SEDI helpers and identifier mapping
    parse/                        # Filing/news parsers
    features/                     # Factor construction modules
    scoring/                      # Composite score calculation
    llm/                          # Lightweight RAG/extractor utilities
    backtest/                     # Toy simulator and metrics
    ui/                           # HTML/Markdown report helpers
    utils/                        # Shared utilities
  tests/                          # pytest suite covering the core modules
  main.py                         # CLI entry point
```

## Getting started

1. Create a virtual environment and install the dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Run the unit test suite to verify the installation:

   ```bash
   pytest -q
   ```

3. Copy `config/settings.example.yaml` to `config/settings.yaml` and adjust the SEC user agent and other paths to match your environment.

## Command line interface

The CLI orchestrates the nightly workflow.  Each step accepts local file paths so the pipeline can operate entirely offline for testing purposes.

```bash
python main.py ingest --config config/settings.yaml
python main.py build-features --as-of 2024-09-30 \
  --insiders data/insiders.csv --whales data/13d.csv \
  --thirteenf data/13f.csv --catalysts data/catalysts.csv \
  --financials data/financials.csv --prices data/prices.csv \
  --risk data/risk.csv --out data/features.parquet
python main.py rank --features data/features.parquet --out data/ranked.parquet
python main.py report --features data/features.parquet --top 30 --format html --out reports/watchlist.html
python main.py backtest --prices data/prices.csv --signals data/signals.csv
```

The feature builder expects each CSV to contain at least a `ticker` column.  Additional optional columns (e.g. `trade_date`, `transaction_value`, `shares`, `filing_date`) are mapped onto the feature modules described in `smartmoney/features/`.

## Testing

The automated tests cover

- parsing Form 4 and 13D/G/13F filings,
- insider, whale and catalyst feature construction,
- composite scoring,
- the deterministic backtester,
- the regex-based LLM fallback extractor, and
- ingestion utilities such as the identifier mapping table.

Run `pytest -q` before committing changes to ensure the suite remains green.

## Disclaimer

This project is provided for research purposes only.  The resulting rankings and reports are **not** investment advice.
