"""Command-line interface for the MOOD client."""

import argparse
from collections.abc import Sequence

from mood.client.network import NetworkClient
from mood.client.shell import MUDClientShell
from mood.common.constants import DEFAULT_HOST, DEFAULT_PORT


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the MOOD client."""
    parser = argparse.ArgumentParser(description="Run the MOOD client.")
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help="Server host to connect to.",
    )
    parser.add_argument(
        "--port",
        default=DEFAULT_PORT,
        type=int,
        help="Server TCP port.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the MOOD client from the command line."""
    args = build_parser().parse_args(argv)
    try:
        transport = NetworkClient(host=args.host, port=args.port)
    except OSError as error:
        print(f"Failed to connect to {args.host}:{args.port}: {error}")
        return 1

    try:
        MUDClientShell(transport).cmdloop()
    except KeyboardInterrupt:
        print()
        return 130
    finally:
        transport.close()
    return 0
