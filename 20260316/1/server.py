import shlex

FIELD_SIZE = 10
WEAPONS = {
    "sword": 10,
    "spear": 15,
    "axe": 20,
}


def available_monsters() -> list[str]:
    import cowsay
    return sorted(set(cowsay.list_cows()) | {"jgsbat"})


def parse_addmon_args(parts: list[str], start_index: int = 2) -> tuple[int, int, str, int] | None:
    params: dict[str, str | tuple[str, str]] = {}
    i = start_index

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


class GameServer:
    def __init__(self) -> None:
        self.player_x = 0
        self.player_y = 0
        self.monsters: dict[tuple[int, int], tuple[str, str, int]] = {}

    def _wrap(self, value: int) -> int:
        return value % FIELD_SIZE

    def get_encounter(self) -> tuple[str, str] | None:
        monster = self.monsters.get((self.player_x, self.player_y))
        if monster is None:
            return None
        name, hello, _hp = monster
        return name, hello

    def handle_command(self, line: str) -> list[str]:
        line = line.strip()
        if not line:
            return []

        try:
            parts = shlex.split(line)
        except ValueError:
            return ["Invalid arguments"]

        command = parts[0]

        if command in ("up", "down", "left", "right"):
            if len(parts) != 1:
                return ["Invalid arguments"]

            if command == "up":
                self.player_y = self._wrap(self.player_y - 1)
            elif command == "down":
                self.player_y = self._wrap(self.player_y + 1)
            elif command == "left":
                self.player_x = self._wrap(self.player_x - 1)
            else:
                self.player_x = self._wrap(self.player_x + 1)

            lines = [f"Moved to ({self.player_x}, {self.player_y})"]
            encounter = self.get_encounter()
            if encounter is not None:
                name, hello = encounter
                lines.append(f"ENCOUNTER {name} {hello}")
            return lines

        if command == "addmon":
            if len(parts) < 2:
                return ["Invalid arguments"]

            monster_name = parts[1]
            if monster_name not in available_monsters():
                return ["Cannot add unknown monster"]

            parsed = parse_addmon_args(parts)
            if parsed is None:
                return ["Invalid arguments"]

            x, y, hello, hp = parsed
            x = self._wrap(x)
            y = self._wrap(y)

            replaced = (x, y) in self.monsters
            self.monsters[(x, y)] = (monster_name, hello, hp)

            lines = [f"Added monster {monster_name} to ({x}, {y}) saying {hello}"]
            if replaced:
                lines.append("Replaced the old monster")
            return lines

        if command == "attack":
            parsed = parse_attack_args(parts)
            if parsed is None:
                return ["Invalid arguments"]

            monster_name, weapon_name = parsed

            if weapon_name not in WEAPONS:
                return ["Unknown weapon"]

            pos = (self.player_x, self.player_y)
            monster = self.monsters.get(pos)

            if monster is None:
                if monster_name is None:
                    return ["No monster here"]
                return [f"No {monster_name} here"]

            current_name, hello, hp = monster

            if monster_name is not None and current_name != monster_name:
                return [f"No {monster_name} here"]

            damage = min(WEAPONS[weapon_name], hp)
            hp -= damage

            lines = [f"Attacked {current_name}, damage {damage} hp"]

            if hp == 0:
                lines.append(f"{current_name} died")
                del self.monsters[pos]
            else:
                self.monsters[pos] = (current_name, hello, hp)
                lines.append(f"{current_name} now has {hp}")

            return lines

        return ["Invalid command"]