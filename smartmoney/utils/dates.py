"""Date helpers shared across modules."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Iterator

import pandas as pd

WEEKEND = {5, 6}


def to_date(value: date | datetime | str) -> date:
    """Coerce a value to :class:`datetime.date`."""

    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    ts = pd.to_datetime(value)
    if isinstance(ts, pd.Timestamp):
        return ts.date()
    raise TypeError(f"Unsupported date value: {value!r}")


def snap_asof(value: date | datetime | str) -> date:
    """Snap an :code:`as_of` date to the previous trading day."""

    as_of = to_date(value)
    while as_of.weekday() in WEEKEND:
        as_of -= timedelta(days=1)
    return as_of


def iter_month_starts(start: date, end: date) -> Iterator[date]:
    """Yield the first trading day of each month in ``[start, end]``."""

    start = snap_asof(start)
    end = snap_asof(end)
    current = date(start.year, start.month, 1)
    while current <= end:
        yield snap_asof(current)
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)


def days_between(start: date | datetime | str, end: date | datetime | str) -> int:
    """Return the inclusive distance in days between two values."""

    start_date = to_date(start)
    end_date = to_date(end)
    return (end_date - start_date).days


__all__ = ["to_date", "snap_asof", "iter_month_starts", "days_between"]
