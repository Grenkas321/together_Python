import json
import shlex
import socket

FIELD_SIZE = 10


class GameServer:
    def __init__(self) -> None:
        self.player_x = 0
        self.player_y = 0
        self.monsters: dict[tuple[int, int], tuple[str, str, int]] = {}

    def _wrap(self, value: int) -> int:
        return value % FIELD_SIZE

    def handle_command(self, line: str) -> dict:
        parts = shlex.split(line)
        command = parts[0]

        if command == "move":
            dx = int(parts[1])
            dy = int(parts[2])

            self.player_x = self._wrap(self.player_x + dx)
            self.player_y = self._wrap(self.player_y + dy)

            encounter = None
            monster = self.monsters.get((self.player_x, self.player_y))
            if monster is not None:
                name, hello, _hp = monster
                encounter = {
                    "name": name,
                    "hello": hello,
                }

            return {
                "type": "move",
                "x": self.player_x,
                "y": self.player_y,
                "encounter": encounter,
            }

        if command == "addmon":
            monster_name = parts[1]
            x = self._wrap(int(parts[2]))
            y = self._wrap(int(parts[3]))
            hp = int(parts[4])
            hello = parts[5]

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
            requested_name = parts[1]
            damage_limit = int(parts[2])

            pos = (self.player_x, self.player_y)
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

        return {
            "type": "error",
            "message": "Invalid command",
        }


def serve(host: str = "127.0.0.1", port: int = 1337) -> None:
    game = GameServer()

    with socket.create_server((host, port)) as server_socket:
        print(f"Server listening on {host}:{port}")

        conn, addr = server_socket.accept()
        with conn:
            print(f"Client connected: {addr}")
            reader = conn.makefile("r", encoding="utf-8")
            writer = conn.makefile("w", encoding="utf-8")

            for line in reader:
                response = game.handle_command(line.rstrip("\n"))
                writer.write(json.dumps(response, ensure_ascii=False) + "\n")
                writer.flush()


if __name__ == "__main__":
    serve()