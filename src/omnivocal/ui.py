"""User-facing helpers for clipboard, notifications, and status output."""

from __future__ import annotations

import shutil
import subprocess
from typing import Iterable

from rich.console import Console

from .config import ClipboardConfig, NotificationsConfig, UIConfig

console = Console()


class UIError(RuntimeError):
    pass


def copy_to_clipboard(text: str, config: ClipboardConfig) -> None:
    if not config.enabled:
        return
    command = shutil.which(config.command) or config.command
    try:
        subprocess.run([command], input=text.encode("utf-8"), check=True)
    except FileNotFoundError as exc:
        raise UIError(f"Clipboard command not found: {config.command}") from exc
    except subprocess.CalledProcessError as exc:
        raise UIError(f"Clipboard command failed: {exc}") from exc


def send_notification(message: str, config: NotificationsConfig) -> None:
    if not config.enabled:
        return
    command = shutil.which(config.command) or config.command
    try:
        subprocess.run([command, config.title, message], check=True)
    except FileNotFoundError as exc:
        raise UIError(f"Notification command not found: {config.command}") from exc
    except subprocess.CalledProcessError as exc:
        raise UIError(f"Notification command failed: {exc}") from exc


def render_status(message: str) -> None:
    console.print(f"[bold cyan]Omnivocal[/]: {message}")


def render_transcription(text: str, segments: Iterable[str], ui_config: UIConfig) -> None:
    console.print("[bold green]Transcription completed![/]")
    console.print(text)
    if ui_config.show_segments:
        console.print("\n[bold]Segments[/]:")
        for segment in segments:
            console.print(f"• {segment}")

__all__ = [
    "copy_to_clipboard",
    "send_notification",
    "render_status",
    "render_transcription",
    "UIError",
]
