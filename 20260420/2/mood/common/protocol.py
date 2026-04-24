"""Helpers for the shared MOOD protocol."""

Payload = dict[str, object]


def error_response(message: str = "Invalid arguments") -> Payload:
    """Return an error payload for the JSON protocol."""
    return {
        "type": "error",
        "message": message,
    }
