"""Tests for the MOOD server core module."""

from io import StringIO
import json
import unittest
from unittest.mock import patch

from mood.server.core import GameServer, Monster
from mood.server.i18n import ServerTranslator


class GameServerMonsterMovementTests(unittest.TestCase):
    """Verify random monster movement and encounter notifications."""

    def test_moving_monsters_are_enabled_by_default(self) -> None:
        """The server should start with wandering monsters enabled."""
        game = GameServer()
        self.assertTrue(game.moving_monsters_enabled)

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

    def test_movemonsters_command_turns_wandering_off(self) -> None:
        """The server should disable wandering monsters on request."""
        game = GameServer()
        player = game.add_player(StringIO())

        response = game.handle_command(player, "movemonsters off")

        self.assertFalse(game.moving_monsters_enabled)
        self.assertEqual(response["type"], "movemonsters")
        game.send_to_player(player, response)
        payload = json.loads(player.writer.getvalue().splitlines()[-1])
        self.assertEqual(payload["message"], "Moving monsters: off")

    def test_movemonsters_command_turns_wandering_on(self) -> None:
        """The server should enable wandering monsters on request."""
        game = GameServer(moving_monsters_enabled=False)
        player = game.add_player(StringIO())

        response = game.handle_command(player, "movemonsters on")

        self.assertTrue(game.moving_monsters_enabled)
        self.assertEqual(response["type"], "movemonsters")
        game.send_to_player(player, response)
        payload = json.loads(player.writer.getvalue().splitlines()[-1])
        self.assertEqual(payload["message"], "Moving monsters: on")


class GameServerLocalizationTests(unittest.TestCase):
    """Verify server-side localization of user-facing messages."""

    def test_hit_points_are_pluralized_for_russian_locale(self) -> None:
        """Russian hit-point forms should use Babel plural rules."""
        translator = ServerTranslator()

        self.assertEqual(
            translator.format_hit_points("ru_RU.UTF8", 1),
            "1 очко здоровья",
        )
        self.assertEqual(
            translator.format_hit_points("ru_RU.UTF8", 2),
            "2 очка здоровья",
        )
        self.assertEqual(
            translator.format_hit_points("ru_RU.UTF8", 5),
            "5 очков здоровья",
        )
        self.assertEqual(
            translator.format_hit_points("ru_RU.UTF8", 21),
            "21 очко здоровья",
        )

    def test_locale_command_switches_player_language(self) -> None:
        """The locale command should change one player's message language."""
        game = GameServer()
        writer = StringIO()
        player = game.add_player(writer)

        response = game.handle_command(player, "locale ru_RU.UTF8")
        game.send_to_player(player, response)

        payload = json.loads(writer.getvalue().splitlines()[-1])
        self.assertEqual(player.locale_name, "ru_RU.UTF8")
        self.assertEqual(payload["type"], "locale")
        self.assertEqual(payload["message"], "Установлена локаль: ru_RU.UTF8")

    def test_addmon_broadcast_is_localized_for_each_player(self) -> None:
        """Broadcast messages should be translated for every recipient."""
        game = GameServer()
        russian_writer = StringIO()
        english_writer = StringIO()
        russian_player = game.add_player(russian_writer)
        game.add_player(english_writer)
        russian_player.locale_name = "ru_RU.UTF8"

        response = game.handle_command(
            russian_player,
            'addmon dragon 1 2 21 "I am dragon"',
        )
        game.send_to_player(russian_player, response)

        russian_payload = json.loads(russian_writer.getvalue().splitlines()[-1])
        observer_payload = json.loads(english_writer.getvalue().splitlines()[-1])

        self.assertEqual(
            russian_payload["messages"][0],
            (
                "Добавлен монстр dragon в (1, 2), говорит I am dragon, "
                "здоровье: 21 очко здоровья"
            ),
        )
        self.assertEqual(
            observer_payload["messages"][0],
            (
                "Added monster dragon to (1, 2) saying I am dragon "
                "with 21 hit points"
            ),
        )

    def test_attack_messages_follow_recipient_locale(self) -> None:
        """Attack notifications should be localized independently per player."""
        game = GameServer()
        attacker_writer = StringIO()
        observer_writer = StringIO()
        attacker = game.add_player(attacker_writer)
        game.add_player(observer_writer)
        attacker.locale_name = "ru_RU.UTF8"
        game.monsters[(0, 0)] = Monster("dragon", "I am dragon", 5)

        response = game.handle_command(attacker, "attack _current_ 2")
        game.send_to_player(attacker, response)

        attacker_payload = json.loads(attacker_writer.getvalue().splitlines()[-1])
        observer_payload = json.loads(observer_writer.getvalue().splitlines()[-1])

        self.assertEqual(
            attacker_payload["messages"],
            [
                "Атакован dragon, урон: 2 очка здоровья",
                "У dragon осталось 3 очка здоровья",
            ],
        )
        self.assertEqual(
            observer_payload["messages"],
            [
                "Attacked dragon, damage 2 hit points",
                "dragon now has 3 hit points",
            ],
        )


if __name__ == "__main__":
    unittest.main()
