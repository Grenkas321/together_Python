"""Tests for shell-level client command translation."""

import unittest
from unittest.mock import MagicMock, call, patch

from mood.client.shell import MUDClientShell


class ClientShellProtocolTests(unittest.TestCase):
    """Verify end-to-end command translation inside the client shell."""

    def _run_shell_session(
        self,
        commands: list[str],
        transport: MagicMock,
    ) -> MagicMock:
        """Run one interactive shell session with mocked user input."""
        shell = MUDClientShell(transport)
        shell.intro = None

        with patch("builtins.input", side_effect=[*commands, "EOF"]):
            with patch("builtins.print") as print_mock:
                shell.cmdloop()

        return print_mock

    def test_addmon_commands_are_translated_before_sending(self) -> None:
        """The shell should translate addmon input into protocol messages."""
        transport = MagicMock()
        transport.request.return_value = {"type": "error", "message": "ignored"}

        with patch("mood.client.commands.cowsay_is_available", return_value=False):
            self._run_shell_session(
                [
                    'addmon dragon hello "I am dragon" hp 30 coords 1 2',
                    'addmon sheep hello "baa baa" hp 5 coords 9 0',
                ],
                transport,
            )

        self.assertEqual(
            transport.request.call_args_list,
            [
                call("addmon dragon 1 2 30 'I am dragon'"),
                call("addmon sheep 9 0 5 'baa baa'"),
            ],
        )

    def test_attack_commands_are_translated_before_sending(self) -> None:
        """The shell should translate attack input into protocol messages."""
        transport = MagicMock()
        transport.request.return_value = {"type": "error", "message": "ignored"}

        self._run_shell_session(
            [
                "attack dragon with axe",
                "attack with spear",
            ],
            transport,
        )

        self.assertEqual(
            transport.request.call_args_list,
            [
                call("attack dragon 20"),
                call("attack _current_ 15"),
            ],
        )

    def test_invalid_attack_parameters_are_reported_without_sending(self) -> None:
        """The shell should reject invalid attack parameters locally."""
        transport = MagicMock()
        transport.request.return_value = {"type": "error", "message": "ignored"}

        print_mock = self._run_shell_session(
            ["attack dragon with spoon"],
            transport,
        )

        transport.request.assert_not_called()
        print_mock.assert_any_call("Unknown weapon")


if __name__ == "__main__":
    unittest.main()
