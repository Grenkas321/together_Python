import sys

import cowsay


FIELD_SIZE = 10


def _wrap(v: int) -> int:
    return v % FIELD_SIZE


def encounter(x: int, y: int) -> None:
    hello = monsters.get((x, y))
    if hello is not None:
        print(cowsay.cowsay(hello))


player_x, player_y = 0, 0
monsters: dict[tuple[int, int], str] = {}


for raw in sys.stdin:
    line = raw.strip()
    if not line:
        continue

    parts = line.split()
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
        if len(parts) != 4:
            print("Invalid arguments")
            continue

        try:
            x = int(parts[1])
            y = int(parts[2])
        except ValueError:
            print("Invalid arguments")
            continue

        hello = parts[3]
        x = _wrap(x)
        y = _wrap(y)

        replaced = (x, y) in monsters
        monsters[(x, y)] = hello

        print(f"Added monster to ({x}, {y}) saying {hello}")
        if replaced:
            print("Replaced the old monster")

        continue

    print("Invalid command")