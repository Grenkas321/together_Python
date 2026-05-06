"""Command-line interface for the MOOD client."""

import argparse
from collections.abc import Sequence
from pathlib import Path
import time

from mood.client.network import NetworkClient
from mood.client.shell import MUDClientShell
from mood.common.constants import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    SCRIPT_COMMAND_INTERVAL,
)


class CommandFileRunner:
    """Execute scripted client commands from a text file."""

    def __init__(
        self,
        shell: MUDClientShell,
        command_interval: float = SCRIPT_COMMAND_INTERVAL,
    ) -> None:
        """Store the shell and delay used between scripted commands."""
        self.shell = shell
        self.command_interval = command_interval

    def _iter_commands(self, path: Path) -> Sequence[str]:
        """Read commands from a file, skipping empty lines and comments."""
        commands: list[str] = []
        with path.open("r", encoding="utf-8") as file_obj:
            for raw_line in file_obj:
                command = raw_line.strip()
                if not command or command.startswith("#"):
                    continue
                commands.append(command)
        return commands

    def run(self, path: Path) -> int:
        """Run commands from ``path`` without entering interactive mode."""
        last_sent_at: float | None = None
        for command in self._iter_commands(path):
            if last_sent_at is not None:
                elapsed = time.monotonic() - last_sent_at
                if elapsed < self.command_interval:
                    time.sleep(self.command_interval - elapsed)

            print(f"{self.shell.prompt}{command}")
            if self.shell.run_command(command):
                last_sent_at = time.monotonic()
        return 0


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
    parser.add_argument(
        "--file",
        type=Path,
        help="Read commands from a .mood script file.",
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
        shell = MUDClientShell(transport)
        if args.file is not None:
            try:
                return CommandFileRunner(shell).run(args.file)
            except OSError as error:
                print(f"Failed to read {args.file}: {error}")
                return 1

        shell.cmdloop()
    except KeyboardInterrupt:
        print()
        return 130
    finally:
        transport.close()
    return 0
