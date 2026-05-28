"""Privacy guards — reject sensitive payloads."""

FORBIDDEN_METADATA_KEYS = frozenset({
    "password", "passwd", "secret", "token", "api_key", "apikey",
    "file_content", "contents", "body", "keystroke", "keystrokes",
    "screenshot", "clipboard", "browser_history", "private_message",
    "credential", "credentials", "private_key", "access_token",
    "refresh_token", "session_token",
})

FORBIDDEN_TOP_LEVEL_KEYS = frozenset({
    "password", "file_content", "keystrokes", "screenshot", "clipboard",
})


def assert_safe_metadata(metadata: dict) -> None:
    _check_dict(metadata, path="metadata")


def _check_dict(d: dict, path: str) -> None:
    for key, value in d.items():
        key_lower = key.lower().replace("-", "_")
        if key_lower in FORBIDDEN_METADATA_KEYS:
            raise ValueError(f"Forbidden metadata key at {path}.{key}")
        if isinstance(value, dict):
            _check_dict(value, f"{path}.{key}")
