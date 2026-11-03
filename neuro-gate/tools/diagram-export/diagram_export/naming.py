"""Deterministic PNG naming."""

import re
from pathlib import Path

from .models import DiagramSource


def slug(value: str) -> str:
    """Convert arbitrary source text to a safe lowercase filename component."""
    value = re.sub(r"^\d+[.)-]?\s*", "", value.lower())
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "diagram"


def output_names(sources: list[DiagramSource]) -> dict[str, str]:
    """Assign stable unique PNG names to canonical sources."""
    names: dict[str, str] = {}
    used: set[str] = set()
    for source in sources:
        if not source.canonical:
            continue
        if source.origin == "standalone":
            stem = Path(source.path).stem.lower()
            base = re.sub(r"[^a-z0-9-]+", "-", stem).strip("-")
        else:
            prefix = Path(source.path).stem.split("-", 1)[0]
            base = f"{slug(prefix)}-{slug(source.document_heading or 'diagram')}"
        candidate = f"{base}.png"
        suffix = 2
        while candidate in used:
            candidate = f"{base}-{suffix}.png"
            suffix += 1
        used.add(candidate)
        names[source.source_id] = candidate
    return names
