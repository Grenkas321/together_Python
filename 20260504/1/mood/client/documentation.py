"""Open packaged MOOD documentation in a browser."""

import webbrowser
from importlib.resources import as_file, files


def documentation_index() -> str:
    """Return the packaged HTML documentation index path."""
    index = files("mood.docs").joinpath("html", "index.html")
    with as_file(index) as path:
        return str(path)


def open_documentation() -> bool:
    """Open generated documentation in the default browser."""
    return webbrowser.open(documentation_index())
