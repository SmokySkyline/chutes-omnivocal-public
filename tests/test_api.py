import base64
import json
from pathlib import Path

import pytest
import requests

from omnivocal.api import ChutesAPIError, ChutesClient
from omnivocal.config import ChutesConfig


def test_encode_and_transcribe(monkeypatch, tmp_path):
    tmp_file = tmp_path / "audio.wav"
    tmp_file.write_bytes(b"data")

    config = ChutesConfig(api_key="key", endpoint="https://example.com")
    client = ChutesClient(config)

    class DummyResponse:
        def __init__(self):
            self.status_code = 200
            self.headers = {'content-type': 'application/json'}

        def json(self):
            return [{"start": 0.0, "end": 1.0, "text": "hello world"}]

        def raise_for_status(self):
            pass

    def fake_post(url, headers, json, timeout):
        assert url == config.endpoint
        # Check the payload format (flat structure)
        assert "audio_b64" in json
        audio_b64 = json["audio_b64"]
        decoded = base64.b64decode(audio_b64)
        assert decoded == b"data"
        return DummyResponse()

    monkeypatch.setattr(client.session, "post", fake_post)

    result = client.transcribe(tmp_file)
    assert result.text == "hello world"


def test_retries(monkeypatch, tmp_path):
    tmp_file = tmp_path / "audio.wav"
    tmp_file.write_bytes(b"data")

    config = ChutesConfig(api_key="key", endpoint="https://example.com", max_retries=2)
    client = ChutesClient(config)

    class DummyResponse:
        status_code = 500

        def raise_for_status(self):
            raise requests.HTTPError("boom")

    monkeypatch.setattr(client.session, "post", lambda *args, **kwargs: DummyResponse())

    with pytest.raises(ChutesAPIError):
        client.transcribe(tmp_file)
