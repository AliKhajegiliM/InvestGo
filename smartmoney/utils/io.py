"""I/O helpers for configuration and local caching."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
import yaml

DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "config" / "settings.example.yaml"


@dataclass(slots=True)
class DataPaths:
    cache_dir: Path


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def load_config(path: str | Path | None = None, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    config_path = Path(path) if path else DEFAULT_CONFIG
    with open(config_path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if overrides:
        data = _deep_update(dict(data), overrides)
    return data


def _deep_update(target: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            target[key] = _deep_update(dict(target[key]), value)
        else:
            target[key] = value
    return target


def write_dataframe(df: pd.DataFrame, path: str | Path) -> Path:
    dest = Path(path)
    ensure_dir(dest.parent)
    if dest.suffix == ".parquet":
        try:
            df.to_parquet(dest)
        except Exception:  # pragma: no cover - fallback path
            dest = dest.with_suffix(".csv")
            df.to_csv(dest, index=False)
    else:
        df.to_csv(dest, index=False)
    return dest


def read_dataframe(path: str | Path) -> pd.DataFrame:
    src = Path(path)
    if src.suffix == ".parquet":
        try:
            return pd.read_parquet(src)
        except Exception:  # pragma: no cover - fallback path
            src = src.with_suffix(".csv")
    return pd.read_csv(src)


__all__ = [
    "DataPaths",
    "ensure_dir",
    "load_config",
    "read_dataframe",
    "write_dataframe",
]
