"""Audio capture and processing for Omnivocal."""

from __future__ import annotations

import contextlib
import time
import wave
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import numpy as np
except ImportError as exc:  # pragma: no cover
    np = None  # type: ignore[assignment]
    _NUMPY_IMPORT_ERROR = exc
else:  # pragma: no cover
    _NUMPY_IMPORT_ERROR = None

try:
    import sounddevice as sd
except ImportError as exc:  # pragma: no cover
    sd = None  # type: ignore[assignment]
    _SD_IMPORT_ERROR = exc
else:  # pragma: no cover
    _SD_IMPORT_ERROR = None

try:
    import webrtcvad
except ImportError:  # pragma: no cover
    webrtcvad = None  # type: ignore[assignment]

from .config import RecordingConfig, VadConfig


class AudioError(RuntimeError):
    """Raised when audio recording fails or dependencies are missing."""


class Recorder:
    """Microphone recorder producing WAV files."""

    def __init__(self, recording_config: RecordingConfig, vad_config: VadConfig) -> None:
        if np is None:
            raise AudioError("numpy dependency is not installed") from _NUMPY_IMPORT_ERROR  # type: ignore[arg-type]
        if sd is None:
            raise AudioError("sounddevice dependency is not installed") from _SD_IMPORT_ERROR  # type: ignore[arg-type]
        if vad_config.enabled and webrtcvad is None:
            raise AudioError("webrtcvad dependency is required for VAD but is not installed")

        self.recording_config = recording_config
        self.vad_config = vad_config
        self.vad = webrtcvad.Vad(vad_config.aggressiveness) if vad_config.enabled and webrtcvad else None

    def record_once(self, temp_dir: Optional[Path] = None) -> Path:
        """Capture audio synchronously and return the recorded file path."""

        temp_directory = Path(temp_dir or self.recording_config.temp_dir)
        temp_directory.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        file_path = temp_directory / f"omnivocal-{timestamp}.wav"
        self._record_to_path(file_path)
        return file_path

    def _record_to_path(self, file_path: Path) -> None:
        duration = self.recording_config.max_seconds
        sample_rate = self.recording_config.sample_rate
        channels = self.recording_config.channels
        block_size = int(sample_rate * 0.02)  # 20ms frames for VAD

        frames = []
        silence_duration = 0.0
        has_detected_speech = False
        recording_finished = False

        def callback(indata, frame_count, time_info, status):  # type: ignore[no-untyped-def]
            nonlocal silence_duration, has_detected_speech, recording_finished
            if status:
                # Log status but don't fail on minor issues
                pass
            
            # Always capture the audio frame
            frames.append(indata.copy())
            
            # VAD logic - only if VAD is enabled
            if self.vad is not None:
                try:
                    # Convert to PCM16 for webrtcvad
                    pcm16 = _float_to_pcm16(indata[:, 0])
                    is_speech = self.vad.is_speech(pcm16, sample_rate)
                    
                    # Track if we've detected speech at least once
                    if is_speech:
                        has_detected_speech = True
                        silence_duration = 0.0
                    # Only count silence after we've detected speech
                    elif has_detected_speech:
                        # frame_count is the blocksize in samples
                        silence_duration += (frame_count / sample_rate)
                        # Stop recording after configured silence duration
                        if silence_duration * 1000 >= self.vad_config.silence_ms_to_stop:
                            recording_finished = True
                            raise sd.CallbackStop
                except Exception:  # pylint: disable=broad-except
                    # If VAD fails, just continue recording
                    pass

        try:
            with sd.InputStream(
                samplerate=sample_rate,
                channels=channels,
                dtype="float32",
                blocksize=block_size,
                callback=callback,
            ) as stream:
                # Instead of sleeping for the full duration, check periodically
                # This allows us to detect when the callback stops the stream
                max_duration = duration
                start_time = time.time()
                
                while stream.active and (time.time() - start_time) < max_duration:
                    if recording_finished:
                        break
                    time.sleep(0.1)  # Check every 100ms
        except sd.CallbackStop:
            # Expected when VAD detects end of speech
            pass
        except Exception as exc:  # pylint: disable=broad-except
            raise AudioError(f"Failed to capture audio: {exc}") from exc

        array_module = np  # type: ignore[assignment]
        signal_data = (
            array_module.concatenate(frames, axis=0)
            if frames
            else array_module.empty((0, channels), dtype=array_module.float32)
        )
        self._write_wav(file_path, signal_data)

    def _write_wav(self, file_path: Path, data):  # type: ignore[no-untyped-def]
        array_module = np  # type: ignore[assignment]
        if not data.size:
            raise AudioError("No audio captured")
        sample_rate = self.recording_config.sample_rate
        channels = self.recording_config.channels
        flattened = data[:, 0] if channels == 1 else data.reshape(-1)
        pcm_data = _float_to_pcm16(flattened)
        with contextlib.closing(wave.open(str(file_path), "wb")) as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(pcm_data)


def _float_to_pcm16(data):  # type: ignore[no-untyped-def]
    array_module = np  # type: ignore[assignment]
    data = array_module.clip(data, -1.0, 1.0)
    pcm = (data * 32767.0).astype(array_module.int16)
    return pcm.tobytes()


__all__ = ["Recorder", "AudioError"]
