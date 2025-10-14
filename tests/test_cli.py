from pathlib import Path

import pytest

from omnivocal.cli import build_parser


def test_build_parser_commands():
    parser = build_parser()
    commands = {action.dest for action in parser._subparsers._group_actions[0]._choices_actions}  # type: ignore[attr-defined]
    expected = {"once", "config", "doctor", "test-api", "status"}
    assert expected.issubset(commands)
    # Verify removed commands are not present
    assert "start" not in commands
    assert "stop" not in commands
    assert "toggle" not in commands
