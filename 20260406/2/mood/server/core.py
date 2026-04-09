"""Server-side game logic for MOOD."""

import json
import random
import shlex
import socket
import threading
from dataclasses import dataclass, field
from typing import TextIO

from mood.common.constants import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    FIELD_SIZE,
    MONSTER_MOVE_INTERVAL,
)
from mood.common.protocol import Payload, error_response

Position = tuple[int, int]
DIRECTION_STEPS = (
    ("right", 1, 0),
    ("left", -1, 0),
    ("up", 0, -1),
    ("down", 0, 1),
)


@dataclass(slots=True)
class Monster:
    """Represent a monster placed on the playing field."""

    name: str
    hello: str
    hp: int


@dataclass(slots=True)
class Player:
    """Represent a connected player."""

    name: str
    writer: TextIO
    x: int = 0
    y: int = 0
    send_lock: threading.Lock = field(default_factory=threading.Lock)


class GameServer:
    """Store the shared game state for all players."""

    def __init__(self, monster_move_interval: float = MONSTER_MOVE_INTERVAL) -> None:
        """Initialize the in-memory game state."""
        self.monsters: dict[Position, Monster] = {}
        self.players: dict[str, Player] = {}
        self.lock = threading.Lock()
        self.next_player_id = 1
        self.monster_move_interval = monster_move_interval
        self.stop_event = threading.Event()
        self.monster_thread: threading.Thread | None = None

    def wrap_position(self, value: int) -> int:
        """Wrap a coordinate around the toroidal playing field."""
        return value % FIELD_SIZE

    def add_player(self, writer: TextIO) -> Player:
        """Create and register a new player for a client connection."""
        with self.lock:
            name = f"player{self.next_player_id}"
            self.next_player_id += 1
            player = Player(name=name, writer=writer)
            self.players[name] = player
            return player

    def remove_player(self, player: Player) -> None:
        """Remove a disconnected player from the game state."""
        with self.lock:
            self.players.pop(player.name, None)

    def send_to_player(self, player: Player, payload: Payload) -> None:
        """Send a JSON payload to a single player."""
        try:
            with player.send_lock:
                player.writer.write(json.dumps(payload, ensure_ascii=False) + "\n")
                player.writer.flush()
        except OSError:
            pass

    def broadcast(self, payload: Payload) -> None:
        """Send a payload to every connected player."""
        with self.lock:
            players = list(self.players.values())

        for player in players:
            self.send_to_player(player, payload)

    def _handle_move(self, player: Player, parts: list[str]) -> Payload:
        """Handle a player movement command."""
        if len(parts) != 3:
            return error_response()

        try:
            dx = int(parts[1])
            dy = int(parts[2])
        except ValueError:
            return error_response()

        with self.lock:
            player.x = self.wrap_position(player.x + dx)
            player.y = self.wrap_position(player.y + dy)

            encounter = None
            monster = self.monsters.get((player.x, player.y))
            if monster is not None:
                encounter = {
                    "name": monster.name,
                    "hello": monster.hello,
                }

            return {
                "type": "move",
                "x": player.x,
                "y": player.y,
                "encounter": encounter,
                }

    def _handle_addmon(self, parts: list[str]) -> Payload:
        """Handle the command that creates or replaces a monster."""
        if len(parts) != 6:
            return error_response()

        monster_name = parts[1]

        try:
            x = self.wrap_position(int(parts[2]))
            y = self.wrap_position(int(parts[3]))
            hp = int(parts[4])
        except ValueError:
            return error_response()

        if hp <= 0:
            return error_response()

        hello = parts[5]

        with self.lock:
            replaced = (x, y) in self.monsters
            self.monsters[(x, y)] = Monster(monster_name, hello, hp)

        return {
            "type": "addmon",
            "name": monster_name,
            "x": x,
            "y": y,
            "hello": hello,
            "replaced": replaced,
        }

    def _handle_attack(self, player: Player, parts: list[str]) -> Payload:
        """Handle a player attack against a monster on the same cell."""
        if len(parts) != 3:
            return error_response()

        requested_name = parts[1]

        try:
            damage_limit = int(parts[2])
        except ValueError:
            return error_response()

        if damage_limit <= 0:
            return error_response()

        with self.lock:
            position = (player.x, player.y)
            monster = self.monsters.get(position)

            if monster is None:
                return {
                    "type": "attack",
                    "result": "no_monster",
                    "name": None if requested_name == "_current_" else requested_name,
                }

            if requested_name != "_current_" and requested_name != monster.name:
                return {
                    "type": "attack",
                    "result": "no_monster",
                    "name": requested_name,
                }

            damage = min(damage_limit, monster.hp)
            monster.hp -= damage

            if monster.hp == 0:
                del self.monsters[position]

        return {
            "type": "attack",
            "result": "ok",
            "name": monster.name,
            "damage": damage,
            "hp": monster.hp,
        }

    def _handle_sayall(self, player: Player, parts: list[str]) -> Payload:
        """Handle a broadcast chat message from a player."""
        if len(parts) != 2:
            return error_response()

        message = parts[1]
        self.broadcast(
            {
                "type": "sayall",
                "from": player.name,
                "message": message,
            }
        )
        return {
            "type": "sayall",
            "result": "ok",
        }

    def _players_at_position(self, position: Position) -> list[Player]:
        """Return all players currently standing on a given cell."""
        return [
            player
            for player in self.players.values()
            if (player.x, player.y) == position
        ]

    def _build_encounter_payload(self, monster: Monster) -> Payload:
        """Build a payload describing a monster encounter."""
        return {
            "type": "encounter",
            "name": monster.name,
            "hello": monster.hello,
        }

    def move_random_monster(self) -> bool:
        """Move a random monster one cell and notify affected players.

        Returns ``True`` when a monster was moved successfully and ``False``
        when movement was impossible, for example because there are no
        monsters on the field.
        """
        with self.lock:
            if not self.monsters:
                return False
            if len(self.monsters) >= FIELD_SIZE * FIELD_SIZE:
                return False

            positions = list(self.monsters.keys())
            while True:
                old_position = random.choice(positions)
                direction, dx, dy = random.choice(DIRECTION_STEPS)
                new_position = (
                    self.wrap_position(old_position[0] + dx),
                    self.wrap_position(old_position[1] + dy),
                )
                if new_position in self.monsters:
                    continue

                monster = self.monsters.pop(old_position)
                self.monsters[new_position] = monster
                encountered_players = self._players_at_position(new_position)
                movement_payload = {
                    "type": "monster_move",
                    "name": monster.name,
                    "direction": direction,
                    "message": f"{monster.name} moved one cell {direction}",
                }
                encounter_payload = self._build_encounter_payload(monster)
                break

        self.broadcast(movement_payload)
        for player in encountered_players:
            self.send_to_player(player, encounter_payload)
        return True

    def _monster_wander_loop(self) -> None:
        """Periodically move monsters until the server is stopped."""
        while not self.stop_event.wait(self.monster_move_interval):
            self.move_random_monster()

    def start_monster_wanderer(self) -> None:
        """Start the background thread that moves monsters."""
        if self.monster_thread is not None and self.monster_thread.is_alive():
            return
        self.stop_event.clear()
        self.monster_thread = threading.Thread(
            target=self._monster_wander_loop,
            daemon=True,
        )
        self.monster_thread.start()

    def stop_monster_wanderer(self) -> None:
        """Stop the background thread that moves monsters."""
        self.stop_event.set()
        if self.monster_thread is None:
            return
        self.monster_thread.join(timeout=1.0)

    def handle_command(self, player: Player, line: str) -> Payload | None:
        """Parse and execute a single protocol command from a player."""
        try:
            parts = shlex.split(line)
        except ValueError:
            return error_response()

        if not parts:
            return None

        command = parts[0]

        if command == "move":
            return self._handle_move(player, parts)
        if command == "addmon":
            return self._handle_addmon(parts)
        if command == "attack":
            return self._handle_attack(player, parts)
        if command == "sayall":
            return self._handle_sayall(player, parts)
        return error_response("Invalid command")


def handle_client_connection(
    game: GameServer,
    connection: socket.socket,
    address: tuple[str, int],
) -> None:
    """Serve protocol messages for a single client connection."""
    with connection:
        reader = connection.makefile("r", encoding="utf-8")
        writer = connection.makefile("w", encoding="utf-8")

        player = game.add_player(writer)
        print(f"Client connected: {address}, name={player.name}")

        try:
            for line in reader:
                try:
                    response = game.handle_command(player, line.rstrip("\n"))
                except Exception as error:
                    print(f"Error while handling command from {player.name}: {error}")
                    response = error_response("Server error")

                if response is not None:
                    game.send_to_player(player, response)
        finally:
            print(f"Client disconnected: {address}, name={player.name}")
            game.remove_player(player)


def serve(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
    """Start the MOOD server and serve clients forever."""
    game = GameServer()
    game.start_monster_wanderer()
    try:
        with socket.create_server((host, port)) as server_socket:
            print(f"Server listening on {host}:{port}")
            while True:
                connection, address = server_socket.accept()
                thread = threading.Thread(
                    target=handle_client_connection,
                    args=(game, connection, address),
                    daemon=True,
                )
                thread.start()
    finally:
        game.stop_monster_wanderer()
