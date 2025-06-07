"""Parcelizer package."""
from importlib.metadata import PackageNotFoundError, version

__all__ = ["__version__"]
try:
    __version__ = version("parcelizer")
except PackageNotFoundError:  # pragma: no cover - not installed
    __version__ = "0.0.0"
