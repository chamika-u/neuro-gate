"""Subprocess wrapper for Mermaid CLI and PNG validation."""

from __future__ import annotations

import struct
import subprocess
from pathlib import Path

from .errors import ConfigurationError, RenderError


def png_dimensions(path: Path) -> tuple[int, int]:
    """Read dimensions from a PNG header."""
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n" or len(data) < 24:
        raise RenderError(f"invalid PNG output: {path.name}")
    return struct.unpack(">II", data[16:24])


def render(source: str, destination: Path, scale: int, timeout: int, tool_dir: Path) -> tuple[int, int, int]:
    """Render one Mermaid source to a validated PNG."""
    mmdc = tool_dir / "node_modules" / ".bin" / ("mmdc.cmd" if __import__("os").name == "nt" else "mmdc")
    if not mmdc.exists():
        raise ConfigurationError("Mermaid CLI is missing; run npm ci in tools/diagram-export")
    input_path = destination.with_suffix(".mmd")
    input_path.write_text(source, encoding="utf-8")
    try:
        subprocess.run(
            [str(mmdc), "-i", str(input_path), "-o", str(destination), "-s", str(scale),
             "--cssFile", str(tool_dir / "mermaid-fonts.css")],
            check=True, capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise RenderError(f"render timed out after {timeout}s") from exc
    except subprocess.CalledProcessError as exc:
        raise RenderError((exc.stderr or "Mermaid rendering failed").strip()) from exc
    if not destination.is_file() or destination.stat().st_size == 0:
        raise RenderError(f"renderer produced no PNG: {destination.name}")
    width, height = png_dimensions(destination)
    return width, height, destination.stat().st_size
