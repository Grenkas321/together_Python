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

    def handle_command(self, line: str) -> list[str]:
        parts = shlex.split(line)
        command = parts[0]

        if command == "move":
            dx = int(parts[1])
            dy = int(parts[2])

            self.player_x = self._wrap(self.player_x + dx)
            self.player_y = self._wrap(self.player_y + dy)

            lines = [f"MOVED {self.player_x} {self.player_y}"]

            monster = self.monsters.get((self.player_x, self.player_y))
            if monster is not None:
                name, hello, _hp = monster
                lines.append(f"ENCOUNTER {name} {hello}")

            return lines

        if command == "addmon":
            monster_name = parts[1]
            x = self._wrap(int(parts[2]))
            y = self._wrap(int(parts[3]))
            hp = int(parts[4])
            hello = parts[5]

            replaced = (x, y) in self.monsters
            self.monsters[(x, y)] = (monster_name, hello, hp)

            lines = [f"ADDED {monster_name} {x} {y} {hello}"]
            if replaced:
                lines.append("REPLACED")
            return lines

        if command == "attack":
            requested_name = parts[1]
            damage_limit = int(parts[2])

            pos = (self.player_x, self.player_y)
            monster = self.monsters.get(pos)

            if monster is None:
                if requested_name == "_current_":
                    return ["NO_MONSTER"]
                return [f"NO_MONSTER {requested_name}"]

            current_name, hello, hp = monster

            if requested_name != "_current_" and requested_name != current_name:
                return [f"NO_MONSTER {requested_name}"]

            damage = min(damage_limit, hp)
            hp -= damage

            lines = [f"ATTACKED {current_name} {damage}"]

            if hp == 0:
                lines.append("DIED")
                del self.monsters[pos]
            else:
                self.monsters[pos] = (current_name, hello, hp)
                lines.append(f"HP {hp}")

            return lines

        return ["ERROR Invalid command"]


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