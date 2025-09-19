"""Point-in-time helpers ensuring no look-ahead bias."""

from __future__ import annotations

from functools import wraps
from typing import Callable, TypeVar

import pandas as pd

from .dates import snap_asof

F = TypeVar("F", bound=Callable[..., pd.DataFrame])


def filter_as_of(df: pd.DataFrame, as_of, column: str = "as_of") -> pd.DataFrame:
    if column not in df.columns:
        raise KeyError(f"Column '{column}' not found for point-in-time filtering")
    as_of_date = snap_asof(as_of)
    return df.loc[df[column] <= as_of_date].copy()


def point_in_time(column: str = "as_of") -> Callable[[F], F]:
    """Decorator that filters the returned DataFrame to the requested ``as_of`` date."""

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            as_of = kwargs.get("as_of")
            df = func(*args, **kwargs)
            if as_of is None:
                return df
            if not isinstance(df, pd.DataFrame):
                return df
            return filter_as_of(df, as_of, column=column)

        return wrapper  # type: ignore[misc]

    return decorator


def ensure_sorted(df: pd.DataFrame, by: str = "as_of") -> pd.DataFrame:
    if by in df.columns:
        return df.sort_values(by=by).reset_index(drop=True)
    return df


__all__ = ["filter_as_of", "point_in_time", "ensure_sorted"]
