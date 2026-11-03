"""Discovery, normalization, hashing, and canonicalization of Mermaid sources."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from .models import DiagramSource

FENCE = re.compile(r"^\s*```+\s*mermaid\s*$", re.IGNORECASE)
HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*$")


def normalize(content: str) -> str:
    """Normalize Mermaid source text for stable identity."""
    lines = [line.rstrip() for line in content.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    return "\n".join(lines).strip()


def _source(origin: str, path: str, content: str, order: int, heading: str | None = None,
            block_index: int | None = None) -> DiagramSource:
    normalized = normalize(content)
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return DiagramSource(
        source_id=digest, origin=origin, path=path, document_heading=heading,
        block_index=block_index, content=normalized, content_hash=digest,
        canonical=False, discovery_order=order,
    )


def discover(docs_dir: Path) -> list[DiagramSource]:
    """Discover standalone files and fenced Mermaid blocks in deterministic order."""
    if not docs_dir.is_dir():
        raise FileNotFoundError(f"docs directory does not exist: {docs_dir}")
    found: list[DiagramSource] = []
    order = 0
    for path in sorted(docs_dir.rglob("*.mmd")):
        found.append(_source("standalone", path.relative_to(docs_dir.parent).as_posix(),
                             path.read_text(encoding="utf-8"), order))
        order += 1
    for path in sorted(docs_dir.rglob("*.md")):
        lines = path.read_text(encoding="utf-8").splitlines()
        heading: str | None = None
        index = 0
        while index < len(lines):
            match = HEADING.match(lines[index])
            if match:
                heading = match.group(1).strip()
            if FENCE.match(lines[index]):
                start = index + 1
                end = start
                while end < len(lines) and not lines[end].strip().startswith("```"):
                    end += 1
                if end >= len(lines):
                    raise ValueError(f"unterminated Mermaid fence: {path}")
                found.append(_source("inline", path.relative_to(docs_dir.parent).as_posix(),
                                     "\n".join(lines[start:end]), order, heading, index))
                order += 1
                index = end
            index += 1
    return canonicalize(found)


def canonicalize(sources: list[DiagramSource]) -> list[DiagramSource]:
    """Mark one canonical source per content hash, preferring standalone files."""
    canonical: dict[str, DiagramSource] = {}
    for source in sources:
        current = canonical.get(source.content_hash)
        if current is None or (source.origin == "standalone" and current.origin == "inline"):
            canonical[source.content_hash] = source
    return [source.model_copy(update={"canonical": canonical[source.content_hash] is source})
            for source in sources]
