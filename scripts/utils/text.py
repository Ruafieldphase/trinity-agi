from __future__ import annotations

import re

_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    cleaned = _CONTROL_CHARS.sub(" ", value)
    return " ".join(cleaned.split())
