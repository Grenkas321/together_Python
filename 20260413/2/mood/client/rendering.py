"""Client-side monster rendering helpers for MOOD."""

from io import StringIO

try:
    import cowsay
    from cowsay import read_dot_cow
except ModuleNotFoundError:
    cowsay = None
    read_dot_cow = None


def available_monsters() -> list[str]:
    """Return the list of monsters available to the client."""
    monsters = {"jgsbat"}
    if cowsay is not None:
        monsters.update(cowsay.list_cows())
    return sorted(monsters)


if read_dot_cow is not None:
    JGSBAT = read_dot_cow(
        StringIO(
            """
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
"""
        )
    )
else:
    JGSBAT = None


def render_monster(name: str, text: str) -> str:
    """Render a monster speech bubble for the client."""
    if cowsay is None:
        return f"{name} says: {text}"
    if name == "jgsbat":
        return cowsay.cowsay(text, cowfile=JGSBAT)
    return cowsay.cowsay(text, cow=name)
