"""Tests for the MOOD server core module."""

from io import StringIO
import json
import unittest
from unittest.mock import patch

from mood.server.core import GameServer, Monster


class GameServerMonsterMovementTests(unittest.TestCase):
    """Verify random monster movement and encounter notifications."""

    def test_move_random_monster_broadcasts_direction(self) -> None:
        """A successful move should broadcast its direction to players."""
        game = GameServer()
        observer_writer = StringIO()
        game.add_player(observer_writer)
        game.monsters[(0, 0)] = Monster("dragon", "I am dragon", 30)

        with patch(
            "mood.server.core.random.choice",
            side_effect=[(0, 0), ("right", 1, 0)],
        ):
            moved = game.move_random_monster()

        self.assertTrue(moved)
        self.assertIn((1, 0), game.monsters)

        payload = json.loads(observer_writer.getvalue().splitlines()[0])
        self.assertEqual(payload["type"], "monster_move")
        self.assertEqual(payload["message"], "dragon moved one cell right")

    def test_move_random_monster_retries_when_target_cell_is_busy(self) -> None:
        """The server should retry until it finds a free destination cell."""
        game = GameServer()
        game.monsters[(0, 0)] = Monster("dragon", "I am dragon", 30)
        game.monsters[(1, 0)] = Monster("sheep", "baa", 10)

        with patch(
            "mood.server.core.random.choice",
            side_effect=[
                (0, 0),
                ("right", 1, 0),
                (0, 0),
                ("down", 0, 1),
            ],
        ):
            moved = game.move_random_monster()

        self.assertTrue(moved)
        self.assertIn((0, 1), game.monsters)
        self.assertNotIn((0, 0), game.monsters)

    def test_move_random_monster_sends_encounter_to_players(self) -> None:
        """Players on the destination cell should receive an encounter event."""
        game = GameServer()
        player_writer = StringIO()
        player = game.add_player(player_writer)
        player.x = 1
        player.y = 0
        game.monsters[(0, 0)] = Monster("dragon", "I am dragon", 30)

        with patch(
            "mood.server.core.random.choice",
            side_effect=[(0, 0), ("right", 1, 0)],
        ):
            moved = game.move_random_monster()

        self.assertTrue(moved)
        payloads = [
            json.loads(line)
            for line in player_writer.getvalue().splitlines()
        ]

        self.assertEqual(payloads[0]["type"], "monster_move")
        self.assertEqual(payloads[1]["type"], "encounter")
        self.assertEqual(payloads[1]["name"], "dragon")
        self.assertEqual(payloads[1]["hello"], "I am dragon")


if __name__ == "__main__":
    unittest.main()
