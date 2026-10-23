"""Tests for the package bootstrap."""

from panoptes import __version__
from panoptes.__main__ import build_parser, main


def test_package_version_is_defined() -> None:
    """The package exposes a version string."""
    assert __version__ == "0.1.0"


def test_cli_parser_has_expected_program_name() -> None:
    """The CLI parser uses the public command name."""
    assert build_parser().prog == "panoptes"


def test_cli_version(capsys: object) -> None:
    """The CLI version action writes the current version and exits."""
    import argparse

    try:
        main(["--version"])
    except argparse.ArgumentError:
        raise AssertionError("version action should exit cleanly")
    except SystemExit as exc:
        assert exc.code == 0
    else:
        raise AssertionError("version action should exit the parser")
