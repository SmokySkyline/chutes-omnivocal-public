"""Command line interface for Omnivocal."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console

from .api import ChutesAPIError, ChutesClient
from .audio import AudioError, Recorder
from .config import (
    CONFIG_PATH,
    OmnivocalConfig,
    ensure_config,
    load_config,
    save_config,
    set_config_value,
)
from .ui import copy_to_clipboard, render_status, render_transcription, send_notification

console = Console()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ovstt", description="Omnivocal Speech-to-Text CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    once_parser = subparsers.add_parser("once", help="Record audio until silence detected and transcribe")
    once_parser.add_argument("--language", type=str, help="Language hint for transcription")
    once_parser.add_argument("--temp-dir", type=str, help="Temporary directory override")
    once_parser.add_argument("--auto", action="store_true", help="Auto copy results to clipboard")
    once_parser.add_argument("--no-vad", action="store_true", help="Disable voice activity detection")

    config_parser = subparsers.add_parser("config", help="Configuration commands")
    config_subparsers = config_parser.add_subparsers(dest="config_command", required=True)
    config_subparsers.add_parser("show", help="Display configuration")
    config_subparsers.add_parser("path", help="Show configuration path")
    edit_parser = config_subparsers.add_parser("edit", help="Open configuration in editor")
    edit_parser.add_argument("--editor", help="Editor command")
    set_parser = config_subparsers.add_parser("set", help="Set configuration value")
    set_parser.add_argument("key", help="Config key in section.option format")
    set_parser.add_argument("value", help="Value to set")

    subparsers.add_parser("doctor", help="Run diagnostics")
    subparsers.add_parser("test-api", help="Test Chutes API connectivity")
    subparsers.add_parser("status", help="Show current status")

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config = load_config()
    except Exception as exc:  # pylint: disable=broad-except
        console.print(f"[red]Failed to load configuration: {exc}")
        return 1

    command = args.command

    try:
        if command == "once":
            return _command_once(args, config)
        if command == "config":
            return _command_config(args, config)
        if command == "doctor":
            return _command_doctor(config)
        if command == "test-api":
            return _command_test_api(config)
        if command == "status":
            return _command_status(config)
    except (AudioError, ChutesAPIError) as exc:
        console.print(f"[red]{exc}")
        return 1
    except Exception as exc:  # pylint: disable=broad-except
        console.print(f"[red]Unexpected error: {exc}")
        return 1

    parser.print_help()
    return 0


def _command_once(args, config: OmnivocalConfig) -> int:
    # Enable VAD by default unless --no-vad is specified
    if hasattr(args, 'no_vad') and args.no_vad:
        config.vad.enabled = False
    else:
        config.vad.enabled = True
    
    recorder = Recorder(config.recording, config.vad)
    if config.vad.enabled:
        render_status("Starting recording... (will stop automatically when you stop talking)")
    else:
        render_status("Starting recording... (Press Ctrl+C to stop)")
    
    # Notify user that recording has started
    try:
        send_notification("Recording started", config.notifications)
    except Exception as exc:  # pylint: disable=broad-except
        console.print(f"[yellow]Notification failed: {exc}")
    
    try:
        file_path = recorder.record_once(temp_dir=Path(args.temp_dir) if args.temp_dir else None)
    except KeyboardInterrupt:
        console.print("\n[yellow]Recording interrupted")
        return 1
    except AudioError as exc:
        console.print(f"[red]Recording failed: {exc}")
        return 1
    
    render_status(f"Recorded to {file_path}")
    result = _transcribe_file(file_path, config, language=args.language)
    if args.auto or config.ui.auto_copy:
        copy_to_clipboard(result.text, config.clipboard)
    
    # Cleanup temp file
    try:
        file_path.unlink(missing_ok=True)
    except Exception:  # pylint: disable=broad-except
        pass
    
    return 0


def _command_config(args, config: OmnivocalConfig) -> int:
    subcommand = args.config_command
    if subcommand == "show":
        console.print_json(data=config.to_dict())
        return 0
    if subcommand == "path":
        console.print(str(ensure_config()))
        return 0
    if subcommand == "edit":
        editor = args.editor
        editor_cmd = editor or _default_editor()
        if not editor_cmd:
            console.print("[red]No editor configured. Set EDITOR or pass --editor.")
            return 1
        return os.spawnvp(os.P_WAIT, editor_cmd, [editor_cmd, str(ensure_config())])
    if subcommand == "set":
        try:
            set_config_value(config, args.key, args.value)
            save_config(config)
        except ValueError as exc:
            console.print(f"[red]{exc}")
            return 1
        console.print(f"Updated {args.key}")
        return 0
    return 0


def _command_doctor(config: OmnivocalConfig) -> int:
    issues = []
    if not config.chutes.api_key:
        issues.append("Chutes API key is not set")
    for command in (config.clipboard.command, config.notifications.command):
        if command and not shutil.which(command):
            issues.append(f"Command not found: {command}")
    if issues:
        console.print("[red]Issues detected:")
        for issue in issues:
            console.print(f" - {issue}")
        return 1
    console.print("[green]All systems operational")
    return 0


def _command_test_api(config: OmnivocalConfig) -> int:
    client = ChutesClient(config.chutes)
    with _progress("Testing API"):
        client.test_connection()
    console.print("[green]API connectivity OK")
    return 0


def _command_status(config: OmnivocalConfig) -> int:
    console.print(f"Config path: {CONFIG_PATH}")
    render_status("Ready")
    return 0


def _transcribe_file(file_path: Path, config: OmnivocalConfig, language: Optional[str] = None):
    client = ChutesClient(config.chutes)
    render_status("Transcribing audio...")
    
    # Notify user that transcription has started
    try:
        send_notification("Transcribing audio", config.notifications)
    except Exception as exc:  # pylint: disable=broad-except
        console.print(f"[yellow]Notification failed: {exc}")
    
    try:
        result = client.transcribe(file_path, language=language)
    except ChutesAPIError as exc:
        console.print(f"[red]Transcription failed: {exc}")
        raise
    
    render_transcription(
        result.text,
        (segment.text for segment in result.segments),
        config.ui,
    )
    
    try:
        send_notification("Transcription complete", config.notifications)
    except Exception as exc:  # pylint: disable=broad-except
        console.print(f"[yellow]Notification failed: {exc}")
    
    return result


def _default_editor() -> Optional[str]:
    for env_var in ("VISUAL", "EDITOR"):
        value = os.environ.get(env_var)
        if value:
            return value
    return shutil.which("nano") or shutil.which("vi")


def entrypoint():
    sys.exit(main())


if __name__ == "__main__":
    entrypoint()
