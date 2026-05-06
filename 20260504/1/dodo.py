"""Build automation tasks for MOOD."""

from pathlib import Path
import shutil
import sys


DOIT_CONFIG = {"default_tasks": ["html"]}
PYTHON = f'"{sys.executable}"'

LOCALE_DIR = Path("mood/server/locale")
DOMAIN = "mood_server"
POT_FILE = LOCALE_DIR / f"{DOMAIN}.pot"
PO_FILE = LOCALE_DIR / "ru_RU/LC_MESSAGES" / f"{DOMAIN}.po"
MO_FILE = LOCALE_DIR / "ru_RU/LC_MESSAGES" / f"{DOMAIN}.mo"
DOC_BUILD_DIR = Path("mood/docs")
TEST_STAMP = Path(".doit") / "test.stamp"
I18N_STAMP = Path(".doit") / "i18n.stamp"


def clean_targets(*targets: Path) -> tuple:
    """Return a doit clean action that removes generated target files."""

    def clean() -> None:
        for target in targets:
            Path(target).unlink(missing_ok=True)

    return (clean,)


def source_files(pattern: str) -> list[str]:
    """Return project files matching ``pattern`` without virtualenv files."""
    return [
        str(path)
        for path in Path(".").glob(pattern)
        if ".venv" not in path.parts and "__pycache__" not in path.parts
    ]


def touch(path: Path) -> None:
    """Create or update a stamp file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()


def update_ru_catalog() -> None:
    """Update existing Russian catalog from the freshly generated template."""
    if PO_FILE.exists():
        return
    raise FileNotFoundError(
        f"{PO_FILE} not found; create catalog once with "
        f"`pybabel init -i {POT_FILE} -d {LOCALE_DIR} -D {DOMAIN} -l ru_RU`"
    )


def clean_docs() -> None:
    """Remove generated Sphinx documentation directory."""
    shutil.rmtree(DOC_BUILD_DIR, ignore_errors=True)


def clean_pycache() -> None:
    """Remove Python bytecode caches left by tests."""
    for path in Path(".").rglob("__pycache__"):
        shutil.rmtree(path, ignore_errors=True)


def task_i18n_extract():
    """Extract server messages to a translation template."""
    return {
        "actions": [
            (
                f"{PYTHON} -m babel.messages.frontend extract "
                "-k gettext:2 -k ngettext:2,3 "
                f"-o {POT_FILE} mood/server"
            )
        ],
        "file_dep": source_files("mood/server/**/*.py"),
        "targets": [str(POT_FILE)],
        "clean": [clean_targets(POT_FILE)],
    }


def task_i18n_update():
    """Refresh the Russian translation catalog from the template."""
    return {
        "actions": [
            (
                f"{PYTHON} -m babel.messages.frontend update "
                f"-i {POT_FILE} -d {LOCALE_DIR} -D {DOMAIN} -l ru_RU"
            ),
            (update_ru_catalog,),
            (touch, [I18N_STAMP]),
        ],
        "file_dep": [str(POT_FILE), str(PO_FILE)],
        "targets": [str(I18N_STAMP)],
        "task_dep": ["i18n_extract"],
        "clean": [clean_targets(I18N_STAMP)],
    }


def task_i18n_compile():
    """Compile the Russian translation catalog."""
    return {
        "actions": [
            f"{PYTHON} -m babel.messages.frontend compile -d {LOCALE_DIR} -D {DOMAIN}"
        ],
        "file_dep": [str(PO_FILE)],
        "targets": [str(MO_FILE)],
        "task_dep": ["i18n_update"],
        "clean": [clean_targets(MO_FILE)],
    }


def task_i18n():
    """Generate all server translation artifacts."""
    return {
        "actions": None,
        "task_dep": ["i18n_compile"],
        "clean": True,
    }


def task_html():
    """Generate HTML documentation."""
    return {
        "actions": [f"{PYTHON} -m sphinx -M html docs {DOC_BUILD_DIR}"],
        "file_dep": source_files("docs/**/*.rst")
        + source_files("docs/**/*.py")
        + source_files("mood/**/*.py"),
        "targets": [str(DOC_BUILD_DIR / "html/index.html")],
        "clean": [clean_docs],
    }


def task_test():
    """Run client and server tests against compiled translations."""
    return {
        "actions": [
            f"{PYTHON} -m unittest "
            "test_client_cli test_server_core test_server_integration",
            (touch, [TEST_STAMP]),
        ],
        "file_dep": source_files("mood/**/*.py")
        + source_files("test_*.py")
        + [str(MO_FILE)],
        "targets": [str(TEST_STAMP)],
        "task_dep": ["i18n"],
        "uptodate": [False],
        "clean": [clean_targets(TEST_STAMP), clean_pycache],
    }
