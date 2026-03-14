import cmd
import shlex
from io import StringIO

import cowsay
from cowsay import read_dot_cow

cow = read_dot_cow(StringIO("""
$the_cow = <<EOC;
         $thoughts
          $thoughts
    ,_                    _,
    ) '-._  ,_    _,  _.-' (
    )  _.-'.|\\--//|.'-._  (
     )'   .'\/o\/o\/'.   `(
      ) .' . \====/ . '. (
       )  / <<    >> \  (
        '-._/``  ``\_.-'
  jgs     __\\'--'//__
         (((""`  `"")))
EOC
"""))

FIELD_SIZE = 10
WEAPONS = {
    "sword": 10,
    "spear": 15,
    "axe": 20,
}


class Game:
    def __init__(self) -> None:
        self.player_x = 0
        self.player_y = 0
        self.monsters: dict[tuple[int, int], tuple[str, str, int]] = {}

    def _wrap(self, v: int) -> int:
        return v % FIELD_SIZE

    def encounter(self, x: int, y: int) -> None:
        m = self.monsters.get((x, y))
        if m is None:
            return
        name, hello, _hp = m
        if name == "jgsbat":
            print(cowsay.cowsay(hello, cowfile=cow))
        else:
            print(cowsay.cowsay(hello, cow=name))

    def available_monsters(self) -> list[str]:
        return sorted(set(cowsay.list_cows()) | {"jgsbat"})

    def parse_addmon_args(self, parts: list[str]) -> tuple[int, int, str, int] | None:
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
        if not isinstance(hp_raw, str) or not isinstance(coords_raw, tuple):
            return None

        try:
            hp = int(hp_raw)
            x = int(coords_raw[0])
            y = int(coords_raw[1])
        except ValueError:
            return None

        if hp <= 0:
            return None

        hello_raw = params["hello"]
        if not isinstance(hello_raw, str):
            return None
        hello = hello_raw
        return x, y, hello, hp

def attack(self, parts: list[str]) -> None:
    monster_name = None
    weapon_name = "sword"

    args = parts[1:]

    if not args:
        pass
    elif len(args) == 1:
        if args[0] == "with":
            print("Invalid arguments")
            return
        monster_name = args[0]
    elif len(args) == 2:
        if args[0] != "with":
            print("Invalid arguments")
            return
        weapon_name = args[1]
    elif len(args) == 3:
        if args[1] != "with":
            print("Invalid arguments")
            return
        monster_name = args[0]
        weapon_name = args[2]
    else:
        print("Invalid arguments")
        return

    if weapon_name not in WEAPONS:
        print("Unknown weapon")
        return

    pos = (self.player_x, self.player_y)
    monster = self.monsters.get(pos)

    if monster is None:
        if monster_name is None:
            print("No monster here")
        else:
            print(f"No {monster_name} here")
        return

    current_name, hello, hp = monster

    if monster_name is not None and current_name != monster_name:
        print(f"No {monster_name} here")
        return

    damage = min(WEAPONS[weapon_name], hp)
    hp -= damage

    print(f"Attacked {current_name}, damage {damage} hp")

    if hp == 0:
        print(f"{current_name} died")
        del self.monsters[pos]
    else:
        self.monsters[pos] = (current_name, hello, hp)
        print(f"{current_name} now has {hp}")
    def execute(self, line: str) -> None:
        line = line.strip()
        if not line:
            return

        try:
            parts = shlex.split(line)
        except ValueError:
            print("Invalid arguments")
            return

        command = parts[0]

        if command in ("up", "down", "left", "right"):
            if len(parts) != 1:
                print("Invalid arguments")
                return

            if command == "up":
                self.player_y = self._wrap(self.player_y - 1)
            elif command == "down":
                self.player_y = self._wrap(self.player_y + 1)
            elif command == "left":
                self.player_x = self._wrap(self.player_x - 1)
            else:
                self.player_x = self._wrap(self.player_x + 1)

            print(f"Moved to ({self.player_x}, {self.player_y})")
            self.encounter(self.player_x, self.player_y)
            return

        if command == "addmon":
            if len(parts) < 2:
                print("Invalid arguments")
                return

            monster_name = parts[1]
            if monster_name not in self.available_monsters():
                print("Cannot add unknown monster")
                return

            parsed = self.parse_addmon_args(parts)
            if parsed is None:
                print("Invalid arguments")
                return

            x, y, hello, hp = parsed
            x = self._wrap(x)
            y = self._wrap(y)

            replaced = (x, y) in self.monsters
            self.monsters[(x, y)] = (monster_name, hello, hp)

            print(f"Added monster {monster_name} to ({x}, {y}) saying {hello}")
            if replaced:
                print("Replaced the old monster")
            return

        if command == "attack":
            self.attack(parts)
            return

        print("Invalid command")


class MUDShell(cmd.Cmd):
    intro = "<<< Welcome to Python-MUD 0.1 >>>"
    prompt = "(mud) "

    def __init__(self, game: Game) -> None:
        super().__init__()
        self.game = game

    def do_up(self, arg: str) -> None:
        self.game.execute("up" if not arg else f"up {arg}")

    def do_down(self, arg: str) -> None:
        self.game.execute("down" if not arg else f"down {arg}")

    def do_left(self, arg: str) -> None:
        self.game.execute("left" if not arg else f"left {arg}")

    def do_right(self, arg: str) -> None:
        self.game.execute("right" if not arg else f"right {arg}")

    def do_addmon(self, arg: str) -> None:
        self.game.execute(f"addmon {arg}")

    def do_attack(self, arg: str) -> None:
        self.game.execute("attack" if not arg else f"attack {arg}")

    def complete_attack(self, text: str, line: str, begidx: int, endidx: int) -> list[str]:
        weapons = list(WEAPONS.keys())
        parts = line.split()

        if line.endswith(" "):
            if parts == ["attack"]:
                return ["with"]
            if parts == ["attack", "with"]:
                return weapons

        if len(parts) == 2 and parts[0] == "attack":
            if "with".startswith(text):
                return ["with"]

        if len(parts) == 3 and parts[0] == "attack" and parts[1] == "with":
            return [w for w in weapons if w.startswith(text)]

        return []

    def emptyline(self) -> bool:
        return False

    def do_EOF(self, arg: str) -> bool:
        print()
        return True


if __name__ == "__main__":
    game = Game()
    MUDShell(game).cmdloop()