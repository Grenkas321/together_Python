"""Server-side game logic for MOOD."""

import json
import shlex
import socket
import threading
from dataclasses import dataclass, field
from typing import TextIO

from mood.common.constants import DEFAULT_HOST, DEFAULT_PORT, FIELD_SIZE
from mood.common.protocol import Payload, error_response


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

    def __init__(self) -> None:
        self.monsters: dict[tuple[int, int], tuple[str, str, int]] = {}
        self.players: dict[str, Player] = {}
        self.lock = threading.Lock()
        self.next_player_id = 1

    def _wrap_position(self, value: int) -> int:
        return value % FIELD_SIZE

    def _add_player(self, writer: TextIO) -> Player:
        with self.lock:
            name = f"player{self.next_player_id}"
            self.next_player_id += 1
            player = Player(name=name, writer=writer)
            self.players[name] = player
            return player

    def _remove_player(self, player: Player) -> None:
        with self.lock:
            self.players.pop(player.name, None)

    def _send_to_player(self, player: Player, payload: Payload) -> None:
        try:
            with player.send_lock:
                player.writer.write(json.dumps(payload, ensure_ascii=False) + "\n")
                player.writer.flush()
        except OSError:
            pass

    def _broadcast(self, payload: Payload) -> None:
        with self.lock:
            players = list(self.players.values())

        for player in players:
            self._send_to_player(player, payload)

    def _handle_move(self, player: Player, parts: list[str]) -> Payload:
        if len(parts) != 3:
            return error_response()

        try:
            dx = int(parts[1])
            dy = int(parts[2])
        except ValueError:
            return error_response()

        with self.lock:
            player.x = self._wrap_position(player.x + dx)
            player.y = self._wrap_position(player.y + dy)

            encounter = None
            monster = self.monsters.get((player.x, player.y))
            if monster is not None:
                name, hello, _hp = monster
                encounter = {
                    "name": name,
                    "hello": hello,
                }

            return {
                "type": "move",
                "x": player.x,
                "y": player.y,
                "encounter": encounter,
            }

    def _handle_addmon(self, parts: list[str]) -> Payload:
        if len(parts) != 6:
            return error_response()

        monster_name = parts[1]

        try:
            x = self._wrap_position(int(parts[2]))
            y = self._wrap_position(int(parts[3]))
            hp = int(parts[4])
        except ValueError:
            return error_response()

        if hp <= 0:
            return error_response()

        hello = parts[5]

        with self.lock:
            replaced = (x, y) in self.monsters
            self.monsters[(x, y)] = (monster_name, hello, hp)

        return {
            "type": "addmon",
            "name": monster_name,
            "x": x,
            "y": y,
            "hello": hello,
            "replaced": replaced,
        }

    def _handle_attack(self, player: Player, parts: list[str]) -> Payload:
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

            current_name, hello, hp = monster

            if requested_name != "_current_" and requested_name != current_name:
                return {
                    "type": "attack",
                    "result": "no_monster",
                    "name": requested_name,
                }

            damage = min(damage_limit, hp)
            hp -= damage

            if hp == 0:
                del self.monsters[position]
            else:
                self.monsters[position] = (current_name, hello, hp)

        return {
            "type": "attack",
            "result": "ok",
            "name": current_name,
            "damage": damage,
            "hp": hp,
        }

    def _handle_sayall(self, player: Player, parts: list[str]) -> Payload:
        if len(parts) != 2:
            return error_response()

        message = parts[1]
        self._broadcast(
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

    def _handle_command(self, player: Player, line: str) -> Payload | None:
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


def _handle_client_connection(
    game: GameServer,
    connection: socket.socket,
    address: tuple[str, int],
) -> None:
    with connection:
        reader = connection.makefile("r", encoding="utf-8")
        writer = connection.makefile("w", encoding="utf-8")

        player = game._add_player(writer)
        print(f"Client connected: {address}, name={player.name}")

        try:
            for line in reader:
                try:
                    response = game._handle_command(player, line.rstrip("\n"))
                except Exception as error:
                    print(f"Error while handling command from {player.name}: {error}")
                    response = error_response("Server error")

                if response is not None:
                    game._send_to_player(player, response)
        finally:
            print(f"Client disconnected: {address}, name={player.name}")
            game._remove_player(player)


def serve(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
    """Start the MOOD server and serve clients forever."""
    game = GameServer()
    with socket.create_server((host, port)) as server_socket:
        print(f"Server listening on {host}:{port}")
        while True:
            connection, address = server_socket.accept()
            thread = threading.Thread(
                target=_handle_client_connection,
                args=(game, connection, address),
                daemon=True,
            )
            thread.start()
