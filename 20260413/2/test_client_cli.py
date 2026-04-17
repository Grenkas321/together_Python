"""Tests for the MOOD client command-file mode."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from mood.client.cli import CommandFileRunner, build_parser, main
from mood.client.commands import translate_user_command


class FakeShell:
    """A lightweight shell stub for testing scripted execution."""

    prompt = "(mood) "

    def __init__(self, results: dict[str, bool] | None = None) -> None:
        """Store preconfigured command outcomes."""
        self.commands: list[str] = []
        self.results = results or {}

    def run_command(self, command: str) -> bool:
        """Record a command and return the configured outcome."""
        self.commands.append(command)
        return self.results.get(command, True)


class CommandFileRunnerTests(unittest.TestCase):
    """Verify scripted command execution for the client."""

    def test_runner_skips_comments_and_blank_lines(self) -> None:
        """The runner should execute only meaningful commands."""
        shell = FakeShell()
        runner = CommandFileRunner(shell)
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "commands.mood"
            path.write_text("# comment\n\nup\nleft\n", encoding="utf-8")
            runner.run(path)

        self.assertEqual(shell.commands, ["up", "left"])

    def test_runner_waits_between_successful_commands(self) -> None:
        """The runner should wait before sending the next scripted command."""
        shell = FakeShell(results={"bad": False})
        runner = CommandFileRunner(shell, command_interval=1.0)
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "commands.mood"
            path.write_text("up\nbad\nleft\n", encoding="utf-8")

            monotonic_values = iter([0.0, 0.2, 1.4, 1.5])
            sleeps: list[float] = []

            with patch("mood.client.cli.time.monotonic", side_effect=monotonic_values):
                with patch("mood.client.cli.time.sleep", side_effect=sleeps.append):
                    runner.run(path)

        self.assertEqual(shell.commands, ["up", "bad", "left"])
        self.assertEqual(sleeps, [0.8])

    def test_main_uses_script_mode_without_cmdloop(self) -> None:
        """The client should skip interactive mode when ``--file`` is used."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "commands.mood"
            path.write_text("up\n", encoding="utf-8")

            with patch("mood.client.cli.NetworkClient") as transport_cls:
                with patch("mood.client.cli.MUDClientShell") as shell_cls:
                    shell = shell_cls.return_value
                    shell.prompt = "(mood) "
                    shell.run_command.return_value = True

                    exit_code = main(["--file", str(path)])

        self.assertEqual(exit_code, 0)
        shell.cmdloop.assert_not_called()
        shell.run_command.assert_called_once_with("up")
        transport_cls.return_value.close.assert_called_once_with()


class ClientCommandTranslationTests(unittest.TestCase):
    """Verify translation of client shell commands."""

    def test_translate_movemonsters_command(self) -> None:
        """The client should translate the movemonsters shell command."""
        self.assertEqual(
            translate_user_command("movemonsters on"),
            ("movemonsters on", None),
        )
        self.assertEqual(
            translate_user_command("movemonsters off"),
            ("movemonsters off", None),
        )

    def test_translate_movemonsters_rejects_invalid_arguments(self) -> None:
        """The client should reject malformed movemonsters commands."""
        self.assertEqual(
            translate_user_command("movemonsters maybe"),
            (None, "Invalid arguments"),
        )

    def test_translate_locale_command(self) -> None:
        """The client should pass the locale command through to the server."""
        self.assertEqual(
            translate_user_command("locale ru_RU.UTF8"),
            ("locale ru_RU.UTF8", None),
        )

    def test_translate_locale_rejects_invalid_arguments(self) -> None:
        """The client should reject malformed locale commands."""
        self.assertEqual(
            translate_user_command("locale"),
            (None, "Invalid arguments"),
        )


class ServerCliTests(unittest.TestCase):
    """Verify server command-line options."""

    def test_parser_supports_disabling_wandering_monsters(self) -> None:
        """The parser should expose the deterministic test flag."""
        args = build_parser().parse_args([])
        self.assertFalse(getattr(args, "file", None))

        from mood.server.cli import build_parser as build_server_parser

        server_args = build_server_parser().parse_args(["--no-monster-wander"])
        self.assertTrue(server_args.no_monster_wander)

    def test_server_main_disables_monster_wandering(self) -> None:
        """The server CLI should pass the disable flag to ``serve``."""
        with patch("mood.server.cli.serve") as serve_mock:
            from mood.server.cli import main as server_main

            exit_code = server_main(["--no-monster-wander"])

        self.assertEqual(exit_code, 0)
        serve_mock.assert_called_once_with(
            host="127.0.0.1",
            port=1337,
            enable_monster_wander=False,
        )


if __name__ == "__main__":
    unittest.main()
