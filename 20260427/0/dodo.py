from pathlib import Path
from zipfile import ZipFile

DOIT_CONFIG = {"default_tasks": ["docs"]}

def task_docs():
    """Create documentation"""

    rstpy = list(Path(".").glob("**/*.rst")) + list(Path(".").glob("**/*.py"))

    ext = {"html": "html", "text": "txt"}
    for typ in ("html", "text"):
        yield { "name": f"{typ} doc",
            "actions": [f"sphinx-build -M {typ} doc/source doc/build"],
            "targets": [f"doc/build/{typ}/index.{ext[typ]}"],
            "file_dep": rstpy,
        }

def task_erase():
    """Clean all junk"""

    return {
        "actions": ["rm -rf doc/build *.zip"],
    }

def task_zip():
    """Pull all documentation in zip"""

    def create_zip(filename, files):
        with ZipFile(filename, "w") as zf:
            for f in files:
                zf.write(f)

    files = list(Path("doc/build/html").glob("**"))

    return {
        "actions": [(create_zip, ["docs.zip", files])],
        "task_dep": ["docs"],
    }

