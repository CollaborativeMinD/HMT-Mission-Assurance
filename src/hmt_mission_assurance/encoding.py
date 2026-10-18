"""Bounded JSON handling and content addressing; no target I/O."""

import hashlib
import json
from typing import Any

MAX_INPUT_BYTES = 1048576


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def embedded_json(value: Any) -> str:
    """Preserve JSON meaning while preventing HTML and Markdown delimiters."""
    text = canonical(value)
    for char in ("<", ">", "&", "`"):
        text = text.replace(char, f"\\u{ord(char):04x}")
    return text


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def parse_json(raw: str) -> Any:
    if len(raw.encode("utf-8")) > MAX_INPUT_BYTES:
        raise ValueError("input exceeds 1 MiB")
    return json.loads(raw, object_pairs_hook=unique_object)
