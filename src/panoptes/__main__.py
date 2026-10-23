"""Command-line entry point for PANOPTES.

P0 provides only argument parsing and version reporting. It performs no network
requests or reconnaissance actions.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from panoptes import __version__


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="panoptes",
        description="Passive-first, graph-native reconnaissance framework.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the bootstrap CLI and return a process exit code."""
    build_parser().parse_args(argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
