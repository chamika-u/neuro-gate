"""Exporter errors and stable exit-code mapping."""


class ExportError(Exception):
    """Base class for expected exporter failures."""


class ConfigurationError(ExportError):
    """Raised for invalid setup or unavailable tooling."""


class RenderError(ExportError):
    """Raised when Mermaid cannot render a source."""


def exit_code(error: Exception | None) -> int:
    """Map an expected error to the documented CLI exit code."""
    if error is None:
        return 0
    if isinstance(error, ConfigurationError):
        return 2
    return 1
