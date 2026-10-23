"""Tests for the package bootstrap."""

import pytest

from panoptes import __version__
from panoptes.__main__ import build_parser, main


def test_package_version_is_defined() -> None:
    """The package exposes a version string."""
    assert __version__ == "0.1.0"


def test_cli_parser_has_expected_program_name() -> None:
    """The CLI parser uses the public command name."""
    assert build_parser().prog == "panoptes"


def test_cli_version(capsys: pytest.CaptureFixture[str]) -> None:
    """The CLI version action writes the current version and exits."""
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])

    assert exc_info.value.code == 0
    assert capsys.readouterr().out == "panoptes 0.1.0\n"
