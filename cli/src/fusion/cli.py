"""fusion — the notary. Records, checks, composes; never judges."""
from __future__ import annotations

import argparse
import sys

from . import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fusion",
        description="Fusion — the notary. Records, checks, composes; never judges.",
    )
    parser.add_argument(
        "--version", action="version", version=f"fusion {__version__}"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    parser.parse_args(argv)
    parser.print_help()
    return 0


def main_entry() -> None:  # console-script shim
    sys.exit(main())
