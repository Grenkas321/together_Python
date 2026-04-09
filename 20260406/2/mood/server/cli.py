"""Command-line interface for the MOOD server."""

import argparse
from collections.abc import Sequence

from mood.common.constants import DEFAULT_HOST, DEFAULT_PORT
from mood.server.core import serve


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the MOOD server."""
    parser = argparse.ArgumentParser(description="Run the MOOD server.")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host to bind to.")
    parser.add_argument(
        "--port",
        default=DEFAULT_PORT,
        type=int,
        help="TCP port to listen on.",
    )
    parser.add_argument(
        "--no-monster-wander",
        action="store_true",
        help="Disable automatic wandering monsters for deterministic testing.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the MOOD server from the command line."""
    args = build_parser().parse_args(argv)
    serve(
        host=args.host,
        port=args.port,
        enable_monster_wander=not args.no_monster_wander,
    )
    return 0
