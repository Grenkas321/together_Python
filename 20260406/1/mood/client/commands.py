"""Command parsing helpers for the MOOD client."""

import shlex

from mood.common.constants import WEAPONS
from mood.client.rendering import available_monsters


def _parse_addmon_args(parts: list[str]) -> tuple[int, int, str, int] | None:
    params: dict[str, str | tuple[str, str]] = {}
    index = 2

    while index < len(parts):
        key = parts[index]

        if key == "hello":
            if "hello" in params or index + 1 >= len(parts):
                return None
            params["hello"] = parts[index + 1]
            index += 2
            continue

        if key == "hp":
            if "hp" in params or index + 1 >= len(parts):
                return None
            params["hp"] = parts[index + 1]
            index += 2
            continue

        if key == "coords":
            if "coords" in params or index + 2 >= len(parts):
                return None
            params["coords"] = (parts[index + 1], parts[index + 2])
            index += 3
            continue

        return None

    if "hello" not in params or "hp" not in params or "coords" not in params:
        return None

    hp_raw = params["hp"]
    coords_raw = params["coords"]
    hello_raw = params["hello"]
    if (
        not isinstance(hp_raw, str)
        or not isinstance(coords_raw, tuple)
        or not isinstance(hello_raw, str)
    ):
        return None

    try:
        hp = int(hp_raw)
        x_coord = int(coords_raw[0])
        y_coord = int(coords_raw[1])
    except ValueError:
        return None

    if hp <= 0:
        return None
    return x_coord, y_coord, hello_raw, hp


def _parse_attack_args(parts: list[str]) -> tuple[str | None, str] | None:
    monster_name = None
    weapon_name = "sword"
    arguments = parts[1:]

    if not arguments:
        return monster_name, weapon_name
    if len(arguments) == 1:
        if arguments[0] == "with":
            return None
        monster_name = arguments[0]
        return monster_name, weapon_name
    if len(arguments) == 2:
        if arguments[0] != "with":
            return None
        weapon_name = arguments[1]
        return monster_name, weapon_name
    if len(arguments) == 3:
        if arguments[1] != "with":
            return None
        monster_name = arguments[0]
        weapon_name = arguments[2]
        return monster_name, weapon_name
    return None


def translate_user_command(line: str) -> tuple[str | None, str | None]:
    """Translate a shell command into a server protocol command."""
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
        if cowsay_is_available() and monster_name not in available_monsters():
            return None, "Cannot add unknown monster"

        parsed = _parse_addmon_args(parts)
        if parsed is None:
            return None, "Invalid arguments"

        x_coord, y_coord, hello, hp = parsed
        return (
            f"addmon {monster_name} {x_coord} {y_coord} "
            f"{hp} {shlex.quote(hello)}",
            None,
        )
    if command == "attack":
        parsed = _parse_attack_args(parts)
        if parsed is None:
            return None, "Invalid arguments"

        monster_name, weapon_name = parsed
        if weapon_name not in WEAPONS:
            return None, "Unknown weapon"

        target = monster_name if monster_name is not None else "_current_"
        damage = WEAPONS[weapon_name]
        return f"attack {target} {damage}", None
    if command == "sayall":
        if len(parts) != 2:
            return None, "Invalid arguments"
        return f"sayall {shlex.quote(parts[1])}", None
    return None, "Invalid command"


def cowsay_is_available() -> bool:
    """Return whether cowsay-based validation is available."""
    return len(available_monsters()) > 1
