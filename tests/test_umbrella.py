"""Tests for the WestQuant umbrella package."""
import pytest


def test_import():
    import westquant
    assert westquant.__version__ == "0.1.0a1"


def test_cli_import():
    from westquant.cli import main
    assert callable(main)


def test_doctor_runs():
    from westquant.cli import cmd_doctor
    import argparse
    args = argparse.Namespace()
    result = cmd_doctor(args)
    assert result == 0


def test_plugins_runs():
    from westquant.cli import cmd_plugins
    import argparse
    args = argparse.Namespace()
    result = cmd_plugins(args)
    assert result == 0


def test_version_runs():
    from westquant.cli import cmd_version
    import argparse
    args = argparse.Namespace()
    result = cmd_version(args)
    assert result == 0
