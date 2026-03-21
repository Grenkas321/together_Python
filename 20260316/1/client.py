import cmd
import json
import shlex
import socket
from io import StringIO

import cowsay
from cowsay import read_dot_cow


WEAPONS = {
    "sword": 10,
    "spear": 15,
    "axe": 20,
}


def available_monsters() -> list[str]:
    return sorted(set(cowsay.list_cows()) | {"jgsbat"})


jgsbat = read_dot_cow(StringIO("""
$the_cow = <<EOC;
         $thoughts
          $thoughts
    ,_                    _,
    ) '-._  ,_    _,  _.-' (
    )  _.-'.|\\--//|.'-._  (
     )'   .'\\/o\\/o\\/'.   `(
      ) .' . \\====/ . '. (
       )  / <<    >> \\  (
        '-._/``  ``\\_.-'
  jgs     __\\\\'--'//__
         (((""`  `"")))
EOC
"""))


def render_monster(name: str, text: str) -> str:
    if name == "jgsbat":
        return cowsay.cowsay(text, cowfile=jgsbat)
    return cowsay.cowsay(text, cow=name)


def parse_addmon_args(parts: list[str]) -> tuple[int, int, str, int] | None:
    params: dict[str, str | tuple[str, str]] = {}
    i = 2

    while i < len(parts):
        key = parts[i]

        if key == "hello":
            if "hello" in params or i + 1 >= len(parts):
                return None
            params["hello"] = parts[i + 1]
            i += 2
            continue

        if key == "hp":
            if "hp" in params or i + 1 >= len(parts):
                return None
            params["hp"] = parts[i + 1]
            i += 2
            continue

        if key == "coords":
            if "coords" in params or i + 2 >= len(parts):
                return None
            params["coords"] = (parts[i + 1], parts[i + 2])
            i += 3
            continue

        return None

    if "hello" not in params or "hp" not in params or "coords" not in params:
        return None

    hp_raw = params["hp"]
    coords_raw = params["coords"]
    hello_raw = params["hello"]

    if not isinstance(hp_raw, str) or not isinstance(coords_raw, tuple) or not isinstance(hello_raw, str):
        return None

    try:
        hp = int(hp_raw)
        x = int(coords_raw[0])
        y = int(coords_raw[1])
    except ValueError:
        return None

    if hp <= 0:
        return None

    return x, y, hello_raw, hp


def parse_attack_args(parts: list[str]) -> tuple[str | None, str] | None:
    monster_name = None
    weapon_name = "sword"

    args = parts[1:]

    if not args:
        pass
    elif len(args) == 1:
        if args[0] == "with":
            return None
        monster_name = args[0]
    elif len(args) == 2:
        if args[0] != "with":
            return None
        weapon_name = args[1]
    elif len(args) == 3:
        if args[1] != "with":
            return None
        monster_name = args[0]
        weapon_name = args[2]
    else:
        return None

    return monster_name, weapon_name


def translate_user_command(line: str) -> tuple[str | None, str | None]:
    line = line.strip()
    if not line:
        return None, None

    try:
        parts = shlex.split(line)
    except ValueError:
        return None, "Invalid arguments"

    command = parts[0]

    if command == "up":
        if len(parts) != 1:
            return None, "Invalid arguments"
        return "move 0 -1", None

    if command == "down":
        if len(parts) != 1:
            return None, "Invalid arguments"
        return "move 0 1", None

    if command == "left":
        if len(parts) != 1:
            return None, "Invalid arguments"
        return "move -1 0", None

    if command == "right":
        if len(parts) != 1:
            return None, "Invalid arguments"
        return "move 1 0", None

    if command == "addmon":
        if len(parts) < 2:
            return None, "Invalid arguments"

        monster_name = parts[1]
        if monster_name not in available_monsters():
            return None, "Cannot add unknown monster"

        parsed = parse_addmon_args(parts)
        if parsed is None:
            return None, "Invalid arguments"

        x, y, hello, hp = parsed
        return f"addmon {monster_name} {x} {y} {hp} {shlex.quote(hello)}", None

    if command == "attack":
        parsed = parse_attack_args(parts)
        if parsed is None:
            return None, "Invalid arguments"

        monster_name, weapon_name = parsed

        if weapon_name not in WEAPONS:
            return None, "Unknown weapon"

        target = monster_name if monster_name is not None else "_current_"
        damage = WEAPONS[weapon_name]
        return f"attack {target} {damage}", None

    return None, "Invalid command"


class NetworkClient:
    def __init__(self, host: str = "127.0.0.1", port: int = 1337) -> None:
        self.sock = socket.create_connection((host, port))
        self.reader = self.sock.makefile("r", encoding="utf-8")
        self.writer = self.sock.makefile("w", encoding="utf-8")

    def request(self, line: str) -> dict:
        self.writer.write(line + "\n")
        self.writer.flush()
        response_line = self.reader.readline()
        if not response_line:
            return {"type": "error", "message": "Server disconnected"}
        return json.loads(response_line)

    def close(self) -> None:
        self.reader.close()
        self.writer.close()
        self.sock.close()


class MUDClientShell(cmd.Cmd):
    intro = "<<< Welcome to Python-MUD 0.1 >>>"
    prompt = "(mud) "

    def __init__(self, transport: NetworkClient) -> None:
        super().__init__()
        self.transport = transport

    def _print_response(self, response: dict) -> None:
        response_type = response["type"]

        if response_type == "move":
            print(f"Moved to ({response['x']}, {response['y']})")
            encounter = response["encounter"]
            if encounter is not None:
                print(render_monster(encounter["name"], encounter["hello"]))
            return

        if response_type == "addmon":
            print(
                f"Added monster {response['name']} to ({response['x']}, {response['y']}) "
                f"saying {response['hello']}"
            )
            if response["replaced"]:
                print("Replaced the old monster")
            return

        if response_type == "attack":
            if response["result"] == "no_monster":
                if response["name"] is None:
                    print("No monster here")
                else:
                    print(f"No {response['name']} here")
                return

            print(f"Attacked {response['name']}, damage {response['damage']} hp")
            if response["hp"] == 0:
                print(f"{response['name']} died")
            else:
                print(f"{response['name']} now has {response['hp']}")
            return

        print(response.get("message", "Unknown server response"))

    def _run_user_command(self, line: str) -> None:
        protocol_line, error = translate_user_command(line)
        if error is not None:
            print(error)
            return
        if protocol_line is None:
            return

        response = self.transport.request(protocol_line)
        self._print_response(response)

    def do_up(self, arg: str) -> None:
        self._run_user_command("up" if not arg else f"up {arg}")

    def help_up(self) -> None:
        print("up")
        print("    Move player one cell up.")

    def do_down(self, arg: str) -> None:
        self._run_user_command("down" if not arg else f"down {arg}")

    def help_down(self) -> None:
        print("down")
        print("    Move player one cell down.")

    def do_left(self, arg: str) -> None:
        self._run_user_command("left" if not arg else f"left {arg}")

    def help_left(self) -> None:
        print("left")
        print("    Move player one cell left.")

    def do_right(self, arg: str) -> None:
        self._run_user_command("right" if not arg else f"right {arg}")

    def help_right(self) -> None:
        print("right")
        print("    Move player one cell right.")

    def do_addmon(self, arg: str) -> None:
        self._run_user_command(f"addmon {arg}")

    def help_addmon(self) -> None:
        print('addmon <monster_name> hello <message> hp <hp> coords <x> <y>')
        print('    Example: addmon dragon hello "I am dragon" hp 30 coords 2 3')

    def do_attack(self, arg: str) -> None:
        self._run_user_command("attack" if not arg else f"attack {arg}")

    def help_attack(self) -> None:
        print("attack")
        print("attack with <weapon>")
        print("attack <monster_name>")
        print("attack <monster_name> with <weapon>")
        print("    Weapons: sword, spear, axe")

    def help_help(self) -> None:
        print("help [command]")
        print("    Show help for command.")

    def complete_attack(self, text: str, line: str, begidx: int, endidx: int) -> list[str]:
        before = line[:begidx]

        try:
            tokens = shlex.split(before)
        except ValueError:
            tokens = before.split()

        monsters = available_monsters()
        weapons = list(WEAPONS.keys())

        if line.endswith(" "):
            if tokens == ["attack"]:
                return monsters + ["with"]
            if tokens == ["attack", "with"]:
                return weapons
            if len(tokens) == 2 and tokens[0] == "attack" and tokens[1] != "with":
                return ["with"]
            if len(tokens) == 3 and tokens[0] == "attack" and tokens[2] == "with":
                return weapons

        if len(tokens) == 1 and tokens[0] == "attack":
            return [m for m in monsters if m.startswith(text)] + (
                ["with"] if "with".startswith(text) else []
            )

        if len(tokens) == 2 and tokens[0] == "attack":
            if tokens[1] == "with":
                return [w for w in weapons if w.startswith(text)]
            return [m for m in monsters if m.startswith(text)]

        if len(tokens) == 3 and tokens[0] == "attack" and tokens[2] == "with":
            return [w for w in weapons if w.startswith(text)]

        return []

    def emptyline(self) -> bool:
        return False

    def do_EOF(self, arg: str) -> bool:
        print()
        self.transport.close()
        return True


if __name__ == "__main__":
    transport = NetworkClient()
    try:
        MUDClientShell(transport).cmdloop()
    finally:
        transport.close()