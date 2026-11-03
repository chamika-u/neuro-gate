from diagram_export.errors import ConfigurationError, RenderError, exit_code


def test_exit_code_mapping() -> None:
    assert exit_code(None) == 0
    assert exit_code(RenderError("bad")) == 1
    assert exit_code(ConfigurationError("bad")) == 2
