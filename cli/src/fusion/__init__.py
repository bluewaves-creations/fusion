"""fusion — the reference CLI of the Fusion Convention."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("fusion-cli")
except PackageNotFoundError:  # running from a checkout, not an install
    __version__ = "0.0.0+dev"
