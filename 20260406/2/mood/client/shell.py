"""Interactive shell for the MOOD client."""

import cmd
import shlex

from mood.client.commands import translate_user_command
from mood.client.network import NetworkClient
from mood.client.rendering import available_monsters, render_monster
from mood.common.constants import SHELL_PROMPT, WEAPONS, WELCOME_TEXT
from mood.common.protocol import Payload


class MUDClientShell(cmd.Cmd):
    """Run an interactive MOOD client session."""

    intro = WELCOME_TEXT
    prompt = SHELL_PROMPT

    def __init__(self, transport: NetworkClient) -> None:
        super().__init__()
        self.transport = transport

    def _print_response(self, response: Payload) -> None:
        response_type = response["type"]
        if response_type == "move":
            print(f"Moved to ({response['x']}, {response['y']})")
            encounter = response["encounter"]
            if encounter is not None:
                print(render_monster(encounter["name"], encounter["hello"]))
            return

        if response_type == "addmon":
            print(
                f"Added monster {response['name']} to "
                f"({response['x']}, {response['y']}) saying {response['hello']}"
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

        if response_type == "sayall" and response.get("result") == "ok":
            print("Message sent")
            return

        if response_type == "monster_move":
            print(response["message"])
            return

        if response_type == "encounter":
            print(render_monster(response["name"], response["hello"]))
            return

        print(response.get("message", "Unknown server response"))

    def run_command(self, line: str) -> bool:
        """Parse, send and print the result of a single user command."""
        protocol_line, error = translate_user_command(line)
        if error is not None:
            print(error)
            return False
        if protocol_line is None:
            return False
        response = self.transport.request(protocol_line)
        self._print_response(response)
        return True

    def do_up(self, arg: str) -> None:
        """Move the player one cell up."""
        self.run_command("up" if not arg else f"up {arg}")

    def help_up(self) -> None:
        """Show help for the up command."""
        print("up")
        print("    Move player one cell up.")

    def do_down(self, arg: str) -> None:
        """Move the player one cell down."""
        self.run_command("down" if not arg else f"down {arg}")

    def help_down(self) -> None:
        """Show help for the down command."""
        print("down")
        print("    Move player one cell down.")

    def do_left(self, arg: str) -> None:
        """Move the player one cell left."""
        self.run_command("left" if not arg else f"left {arg}")

    def help_left(self) -> None:
        """Show help for the left command."""
        print("left")
        print("    Move player one cell left.")

    def do_right(self, arg: str) -> None:
        """Move the player one cell right."""
        self.run_command("right" if not arg else f"right {arg}")

    def help_right(self) -> None:
        """Show help for the right command."""
        print("right")
        print("    Move player one cell right.")

    def do_addmon(self, arg: str) -> None:
        """Add a monster to the playing field."""
        self.run_command(f"addmon {arg}")

    def help_addmon(self) -> None:
        """Show help for the addmon command."""
        print('addmon <monster_name> hello <message> hp <hp> coords <x> <y>')
        print('    Example: addmon dragon hello "I am dragon" hp 30 coords 2 3')

    def do_attack(self, arg: str) -> None:
        """Attack the current monster or a named monster."""
        self.run_command("attack" if not arg else f"attack {arg}")

    def help_attack(self) -> None:
        """Show help for the attack command."""
        print("attack")
        print("attack with <weapon>")
        print("attack <monster_name>")
        print("attack <monster_name> with <weapon>")
        print("    Weapons: sword, spear, axe, FIRE SWORD")

    def do_sayall(self, arg: str) -> None:
        """Send a broadcast message to all players."""
        self.run_command(f"sayall {arg}")

    def help_sayall(self) -> None:
        """Show help for the sayall command."""
        print("sayall <message>")
        print("    Send message to all players.")
        print("    Examples:")
        print("    sayall PREVED")
        print('    sayall "Let\'s attack dragon at 5 9"')

    def help_help(self) -> None:
        """Show help for the help command."""
        print("help [command]")
        print("    Show help for command.")

    def complete_attack(
        self,
        text: str,
        line: str,
        begidx: int,
        endidx: int,
    ) -> list[str]:
        """Complete arguments for the attack command."""
        del endidx
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
            return [monster for monster in monsters if monster.startswith(text)] + [
                keyword for keyword in ["with"] if keyword.startswith(text)
            ]
        if len(tokens) == 2 and tokens[0] == "attack":
            if tokens[1] == "with":
                return [weapon for weapon in weapons if weapon.startswith(text)]
            return [monster for monster in monsters if monster.startswith(text)]
        if len(tokens) == 3 and tokens[0] == "attack" and tokens[2] == "with":
            return [weapon for weapon in weapons if weapon.startswith(text)]
        return []

    def completenames(self, text: str, *ignored: object) -> list[str]:
        """Complete top-level shell commands."""
        commands = [
            "up",
            "down",
            "left",
            "right",
            "addmon",
            "attack",
            "sayall",
            "help",
        ]
        return [name for name in commands if name.startswith(text)]

    def complete_sayall(
        self,
        text: str,
        line: str,
        begidx: int,
        endidx: int,
    ) -> list[str]:
        """Disable tab completion for the sayall command."""
        del text, line, begidx, endidx
        return []

    def emptyline(self) -> bool:
        """Ignore an empty command line."""
        return False

    def do_EOF(self, arg: str) -> bool:
        """Exit the client shell on EOF."""
        del arg
        print()
        self.transport.close()
        return True
