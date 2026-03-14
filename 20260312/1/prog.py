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


def _wrap(v: int) -> int:
    return v % FIELD_SIZE


def encounter(x: int, y: int) -> None:
    m = monsters.get((x, y))
    if m is None:
        return
    name, hello, _hp = m
    print(cowsay.cowsay(hello, cow=name))


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


player_x, player_y = 0, 0
monsters: dict[tuple[int, int], tuple[str, str, int]] = {}

print("<<< Welcome to Python-MUD 0.1 >>>")

for raw in sys.stdin:
    line = raw.strip()
    if not line:
        continue

    try:
        parts = shlex.split(line)
    except ValueError:
        print("Invalid arguments")
        continue

    cmd = parts[0]

    if cmd in ("up", "down", "left", "right"):
        if len(parts) != 1:
            print("Invalid arguments")
            continue

        if cmd == "up":
            player_y = _wrap(player_y - 1)
        elif cmd == "down":
            player_y = _wrap(player_y + 1)
        elif cmd == "left":
            player_x = _wrap(player_x - 1)
        else: 
            player_x = _wrap(player_x + 1)

        print(f"Moved to ({player_x}, {player_y})")
        encounter(player_x, player_y)
        continue

    if cmd == "addmon":
        if len(parts) < 2:
            print("Invalid arguments")
            continue

        monster_name = parts[1]
        if monster_name not in cowsay.list_cows():
            print("Cannot add unknown monster")
            continue

        parsed = parse_addmon_args(parts)
        if parsed is None:
            print("Invalid arguments")
            continue

        x, y, hello, hp = parsed
        x = _wrap(x)
        y = _wrap(y)

        replaced = (x, y) in monsters
        monsters[(x, y)] = (monster_name, hello, hp)

        print(f"Added monster {monster_name} to ({x}, {y}) saying {hello}")
        if replaced:
            print("Replaced the old monster")

        continue

    print("Invalid command")

