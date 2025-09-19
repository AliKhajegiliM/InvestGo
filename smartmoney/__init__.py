"""SmartMoney package initialization."""

from __future__ import annotations

from importlib import resources
from pathlib import Path
from typing import Dict, List

from .types import PITFeatures, SecurityId

__all__ = ["PITFeatures", "SecurityId", "get_package_path", "load_text_resource"]


def get_package_path() -> Path:
    """Return the root path of the installed package."""

    return Path(resources.files(__package__))


def load_text_resource(relative: str) -> str:
    """Load a small text resource packaged with :mod:`smartmoney`."""

    package = __package__
    if package is None:
        raise RuntimeError("smartmoney package is not initialised correctly")
    with resources.as_file(resources.files(package).joinpath(relative)) as path:
        return path.read_text(encoding="utf-8")


# re-export common typing aliases for convenience in other modules
SecurityIdDict = Dict[str, SecurityId]
PITFeatureList = List[PITFeatures]
