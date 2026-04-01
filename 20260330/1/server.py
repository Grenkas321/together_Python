import json
import shlex
import socket
import threading

FIELD_SIZE = 10


def error_response(message: str = "Invalid arguments") -> dict[str, str]:
    return {
        "type": "error",
        "message": message,
    }


class Player:
    def __init__(self, name: str, writer) -> None:
        self.name = name
        self.writer = writer
        self.x = 0
        self.y = 0
        self.send_lock = threading.Lock()


class GameServer:
    def __init__(self) -> None:
        self.monsters: dict[tuple[int, int], tuple[str, str, int]] = {}
        self.players: dict[str, Player] = {}
        self.lock = threading.Lock()
        self.next_player_id = 1

    def _wrap(self, value: int) -> int:
        return value % FIELD_SIZE

    def add_player(self, writer) -> Player:
        with self.lock:
            name = f"player{self.next_player_id}"
            self.next_player_id += 1
            player = Player(name, writer)
            self.players[name] = player
            return player

    def remove_player(self, player: Player) -> None:
        with self.lock:
            self.players.pop(player.name, None)

    def send_to_player(self, player: Player, payload: dict) -> None:
        try:
            with player.send_lock:
                player.writer.write(json.dumps(payload, ensure_ascii=False) + "\n")
                player.writer.flush()
        except OSError:
            pass

    def broadcast(self, payload: dict) -> None:
        with self.lock:
            players = list(self.players.values())

        for player in players:
            self.send_to_player(player, payload)

    def handle_command(self, player: Player, line: str) -> dict | None:
        try:
            parts = shlex.split(line)
        except ValueError:
            return error_response()

        if not parts:
            return None

        command = parts[0]

        if command == "move":
            if len(parts) != 3:
                return error_response()

            try:
                dx = int(parts[1])
                dy = int(parts[2])
            except ValueError:
                return error_response()

            with self.lock:
                player.x = self._wrap(player.x + dx)
                player.y = self._wrap(player.y + dy)

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

        if command == "addmon":
            if len(parts) != 6:
                return error_response()

            monster_name = parts[1]

            try:
                x = self._wrap(int(parts[2]))
                y = self._wrap(int(parts[3]))
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

        if command == "attack":
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
                pos = (player.x, player.y)
                monster = self.monsters.get(pos)

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
                    del self.monsters[pos]
                else:
                    self.monsters[pos] = (current_name, hello, hp)

            return {
                "type": "attack",
                "result": "ok",
                "name": current_name,
                "damage": damage,
                "hp": hp,
            }

        if command == "sayall":
            if len(parts) != 2:
                return error_response()

            message = parts[1]

            self.broadcast({
                "type": "sayall",
                "from": player.name,
                "message": message,
            })
            return {
                "type": "sayall",
                "result": "ok",
            }

        return error_response("Invalid command")


def handle_client(game: GameServer, conn: socket.socket, addr) -> None:
    with conn:
        reader = conn.makefile("r", encoding="utf-8")
        writer = conn.makefile("w", encoding="utf-8")

        player = game.add_player(writer)
        print(f"Client connected: {addr}, name={player.name}")

        try:
            for line in reader:
                try:
                    response = game.handle_command(player, line.rstrip("\n"))
                except Exception as exc:
                    print(f"Error while handling command from {player.name}: {exc}")
                    response = error_response("Server error")

                if response is not None:
                    game.send_to_player(player, response)
        finally:
            print(f"Client disconnected: {addr}, name={player.name}")
            game.remove_player(player)


def serve(host: str = "127.0.0.1", port: int = 1337) -> None:
    game = GameServer()

    with socket.create_server((host, port)) as server_socket:
        print(f"Server listening on {host}:{port}")

        while True:
            conn, addr = server_socket.accept()
            thread = threading.Thread(
                target=handle_client,
                args=(game, conn, addr),
                daemon=True,
            )
            thread.start()


if __name__ == "__main__":
    serve()
