"""Integration tests for client-server command handling."""

import json
import multiprocessing
import socket
import time
import unittest

from mood.server.core import run_server


def _find_free_port() -> int:
    """Return a TCP port that is currently available on localhost."""
    with socket.socket() as probe_socket:
        probe_socket.bind(("127.0.0.1", 0))
        return int(probe_socket.getsockname()[1])


class ServerCommandIntegrationTests(unittest.TestCase):
    """Verify protocol-level interaction between a client and the server."""

    host = "127.0.0.1"

    def setUp(self) -> None:
        """Start a fresh local server process and connect a client socket."""
        self.port = _find_free_port()
        self.process = multiprocessing.Process(
            target=run_server,
            kwargs={
                "host": self.host,
                "port": self.port,
                "enable_monster_wander": False,
            },
        )
        self.process.start()
        self.socket = self._connect_to_server()
        self.socket.settimeout(2.0)
        self.reader = self.socket.makefile("r", encoding="utf-8")
        self.writer = self.socket.makefile("w", encoding="utf-8")

        join_payload = self._read_payload()
        self.assertEqual(join_payload["type"], "player_joined")
        self.assertEqual(join_payload["name"], "player1")

    def tearDown(self) -> None:
        """Close the client connection and terminate the server process."""
        if hasattr(self, "writer"):
            self.writer.close()
        if hasattr(self, "reader"):
            self.reader.close()
        if hasattr(self, "socket"):
            self.socket.close()
        if hasattr(self, "process"):
            self.process.terminate()
            self.process.join(timeout=5.0)

    def _connect_to_server(self) -> socket.socket:
        """Retry connecting to the freshly started server process."""
        deadline = time.monotonic() + 5.0
        last_error: OSError | None = None

        while time.monotonic() < deadline:
            try:
                return socket.create_connection((self.host, self.port), timeout=0.2)
            except OSError as error:
                last_error = error
                if not self.process.is_alive():
                    break
                time.sleep(0.05)

        raise AssertionError("Failed to connect to the test server") from last_error

    def _read_payload(self) -> dict[str, object]:
        """Read a single JSON payload line from the connected server."""
        response_line = self.reader.readline()
        self.assertTrue(response_line)
        return json.loads(response_line)

    def _send_command(self, command: str) -> dict[str, object]:
        """Send one protocol command and return the parsed response."""
        self.writer.write(command + "\n")
        self.writer.flush()
        return self._read_payload()

    def test_addmon_command_returns_monster_description(self) -> None:
        """The addmon protocol command should place a nearby monster."""
        payload = self._send_command('addmon dragon 1 0 30 "I am dragon"')

        self.assertEqual(payload["type"], "addmon")
        self.assertEqual(payload["name"], "dragon")
        self.assertEqual(payload["x"], 1)
        self.assertEqual(payload["y"], 0)
        self.assertEqual(payload["hello"], "I am dragon")
        self.assertEqual(payload["hp"], 30)
        self.assertFalse(payload["replaced"])
        self.assertEqual(
            payload["messages"],
            ["Added monster dragon to (1, 0) saying I am dragon with 30 hit points"],
        )

    def test_move_command_reports_encounter_with_monster(self) -> None:
        """Moving onto a monster cell should return encounter data."""
        self._send_command('addmon dragon 1 0 30 "I am dragon"')

        payload = self._send_command("move 1 0")

        self.assertEqual(payload["type"], "move")
        self.assertEqual(payload["x"], 1)
        self.assertEqual(payload["y"], 0)
        self.assertEqual(
            payload["encounter"],
            {
                "name": "dragon",
                "hello": "I am dragon",
            },
        )

    def test_attack_command_returns_damage_and_remaining_hit_points(self) -> None:
        """Attacking a nearby monster should return combat result data."""
        self._send_command('addmon dragon 1 0 20 "I am dragon"')
        self._send_command("move 1 0")

        payload = self._send_command("attack _current_ 10")

        self.assertEqual(payload["type"], "attack")
        self.assertEqual(payload["result"], "ok")
        self.assertEqual(payload["name"], "dragon")
        self.assertEqual(payload["damage"], 10)
        self.assertEqual(payload["hp"], 10)
        self.assertEqual(
            payload["messages"],
            [
                "Attacked dragon, damage 10 hit points",
                "dragon now has 10 hit points",
            ],
        )


if __name__ == "__main__":
    unittest.main()
