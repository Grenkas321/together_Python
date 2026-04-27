def task_docs():
    """Create documentation"""

    return {
        "actions": ["sphinx-build -M html doc/source build"],
    }