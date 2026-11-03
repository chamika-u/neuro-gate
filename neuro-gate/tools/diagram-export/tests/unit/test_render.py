from pathlib import Path

import pytest

from diagram_export.errors import ConfigurationError, RenderError
from diagram_export.render import png_dimensions, render


def test_missing_renderer_is_configuration_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError):
        render("flowchart LR\nA-->B", tmp_path / "out.png", 2, 1, tmp_path)


def test_invalid_png_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "bad.png"
    path.write_bytes(b"not png")
    with pytest.raises(RenderError):
        png_dimensions(path)
