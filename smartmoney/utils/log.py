"""Logging helpers for the SmartMoney project."""

from __future__ import annotations

import logging
from typing import Optional

_DEFAULT_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def configure_logging(level: int = logging.INFO) -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(level=level, format=_DEFAULT_FORMAT)
    else:
        logging.getLogger().setLevel(level)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name or "smartmoney")


__all__ = ["configure_logging", "get_logger"]
