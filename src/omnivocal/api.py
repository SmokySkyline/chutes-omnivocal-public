"""Chutes Whisper Large V3 API integration."""

from __future__ import annotations

import base64
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from requests import Response

from .config import ChutesConfig


class ChutesAPIError(RuntimeError):
    """Raised when the Chutes API returns an error or cannot be reached."""


@dataclass
class Segment:
    id: int
    seek: int
    start: float
    end: float
    text: str
    tokens: List[int] = field(default_factory=list)
    temperature: float | None = None
    avg_logprob: float | None = None
    compression_ratio: float | None = None
    no_speech_prob: float | None = None


@dataclass
class TranscriptionResult:
    text: str
    language: str
    segments: List[Segment]
    processing_time_ms: float | None = None


class ChutesClient:
    """HTTP client for interacting with the Chutes Whisper API."""

    def __init__(self, config: ChutesConfig, session: requests.Session | None = None) -> None:
        self.config = config
        self.session = session or requests.Session()

    def transcribe(self, audio_path: Path, language: Optional[str] = None) -> TranscriptionResult:
        payload: Dict[str, Any] = {
            "audio_b64": _encode_audio(audio_path),
        }
        if language:
            payload["language"] = language
        response_data = self._post_with_retries(payload)
        return _parse_response(response_data)

    def test_connection(self) -> List[Dict[str, Any]]:
        """Perform a lightweight request to validate API connectivity."""

        try:
            response_data = self._post_with_retries({"audio_b64": ""}, expect_empty_audio=True)
        except ChutesAPIError as exc:
            raise
        return response_data

    def _post_with_retries(self, payload: Dict[str, Any], expect_empty_audio: bool = False) -> List[Dict[str, Any]]:
        retries = max(self.config.max_retries, 1)
        last_error: Exception | None = None
        for attempt in range(1, retries + 1):
            try:
                response = self.session.post(
                    self.config.endpoint,
                    headers={"Authorization": f"Bearer {self.config.api_key}", "Content-Type": "application/json"},
                    json=payload,  # Use json= instead of data=json.dumps()
                    timeout=self.config.timeout_seconds,
                )
                _raise_for_status(response)
                
                # Parse JSON response - API returns array of segment objects
                data = response.json()
                
                # Handle empty audio test
                if expect_empty_audio:
                    return []
                
                # Validate response format
                if not isinstance(data, list):
                    raise ChutesAPIError(f"Unexpected API response format: expected list, got {type(data)}")
                
                return data
            except (requests.RequestException, ChutesAPIError, ValueError) as exc:
                last_error = exc
                if attempt >= retries:
                    break
                time.sleep(min(2 ** attempt, 8))
        raise ChutesAPIError(f"Failed to contact Chutes API after {retries} attempts: {last_error}")


def _encode_audio(path: Path) -> str:
    with path.open("rb") as fh:
        return base64.b64encode(fh.read()).decode("ascii")


def _parse_response(data: List[Dict[str, Any]]) -> TranscriptionResult:
    """Parse API response - handles array of segment objects from Chutes API."""
    # API returns array of segments like [{"start": 0.0, "end": 4.94, "text": "..."}]
    segments = [
        Segment(
            id=idx,
            seek=0,
            start=float(segment.get("start", 0.0)),
            end=float(segment.get("end", 0.0)),
            text=segment.get("text", ""),
            tokens=[],
            temperature=segment.get("temperature"),
            avg_logprob=segment.get("avg_logprob"),
            compression_ratio=segment.get("compression_ratio"),
            no_speech_prob=segment.get("no_speech_prob"),
        )
        for idx, segment in enumerate(data)
    ]
    
    # Combine all segment texts
    full_text = "".join(seg.text for seg in segments)
    
    return TranscriptionResult(
        text=full_text.strip(),
        language="",  # Language detection not provided in response
        segments=segments,
        processing_time_ms=None,
    )


def _raise_for_status(response: Response) -> None:
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise ChutesAPIError(f"API request failed: {exc}")


__all__ = [
    "ChutesClient",
    "ChutesAPIError",
    "TranscriptionResult",
    "Segment",
]
