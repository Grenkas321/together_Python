import cmd
import shlex
from io import StringIO

import cowsay
from cowsay import read_dot_cow

from server import GameServer, WEAPONS, available_monsters


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


class MUDClientShell(cmd.Cmd):
    intro = "<<< Welcome to Python-MUD 0.1 >>>"
    prompt = "(mud) "

    def __init__(self, server: GameServer) -> None:
        super().__init__()
        self.server = server

    def _run(self, line: str) -> None:
        for msg in self.server.handle_command(line):
            if msg.startswith("ENCOUNTER "):
                _, name, hello = msg.split(" ", 2)
                print(render_monster(name, hello))
            else:
                print(msg)

    def do_up(self, arg: str) -> None:
        self._run("up" if not arg else f"up {arg}")

    def help_up(self) -> None:
        print("up")
        print("    Move player one cell up.")

    def do_down(self, arg: str) -> None:
        self._run("down" if not arg else f"down {arg}")

    def help_down(self) -> None:
        print("down")
        print("    Move player one cell down.")

    def do_left(self, arg: str) -> None:
        self._run("left" if not arg else f"left {arg}")

    def help_left(self) -> None:
        print("left")
        print("    Move player one cell left.")

    def do_right(self, arg: str) -> None:
        self._run("right" if not arg else f"right {arg}")

    def help_right(self) -> None:
        print("right")
        print("    Move player one cell right.")

    def do_addmon(self, arg: str) -> None:
        self._run(f"addmon {arg}")

    def help_addmon(self) -> None:
        print('addmon <monster_name> hello <message> hp <hp> coords <x> <y>')
        print('    Example: addmon dragon hello "I am dragon" hp 30 coords 2 3')

    def do_attack(self, arg: str) -> None:
        self._run("attack" if not arg else f"attack {arg}")

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
        return True


if __name__ == "__main__":
    server = GameServer()
    MUDClientShell(server).cmdloop()