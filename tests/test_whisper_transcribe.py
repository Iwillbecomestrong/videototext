import sys
from unittest.mock import MagicMock, patch
import pytest
from scripts.whisper_transcribe import (
    format_seconds_to_srt_timestamp,
    segments_to_srt,
    transcribe_audio,
)
from scripts.download_video import prepare_audio_source


def test_format_seconds_to_srt_timestamp():
    assert format_seconds_to_srt_timestamp(0.0) == "00:00:00,000"
    assert format_seconds_to_srt_timestamp(65.432) == "00:01:05,432"
    assert format_seconds_to_srt_timestamp(3661.123) == "01:01:01,123"


def test_segments_to_srt():
    mock_segments = [
        MagicMock(start=1.0, end=3.5, text=" 第一段语音内容 "),
        MagicMock(start=4.0, end=7.2, text=" 第二段语音内容 "),
    ]
    srt = segments_to_srt(mock_segments)
    assert "1\n00:00:01,000 --> 00:00:03,500\n第一段语音内容" in srt
    assert "2\n00:00:04,000 --> 00:00:07,200\n第二段语音内容" in srt


def test_transcribe_audio_uses_faster_whisper_mock():
    mock_model = MagicMock()
    mock_segments = [
        MagicMock(start=0.5, end=2.0, text=" 测试转写 ")
    ]
    mock_model.transcribe.return_value = (iter(mock_segments), MagicMock(language="zh"))
    
    with patch("scripts.whisper_transcribe._get_faster_whisper_model", return_value=mock_model):
        srt = transcribe_audio("fake_audio.wav", model_size="tiny")
        assert "1\n00:00:00,500 --> 00:00:02,000\n测试转写" in srt


def test_transcribe_audio_falls_back_to_openai_whisper():
    mock_openai_whisper = MagicMock()
    mock_whisper_model = MagicMock()
    mock_whisper_model.transcribe.return_value = {
        "segments": [{"start": 1.0, "end": 2.5, "text": "来自openai-whisper转录"}]
    }
    mock_openai_whisper.load_model.return_value = mock_whisper_model

    # Simulate faster_whisper missing, but openai whisper present
    with patch("scripts.whisper_transcribe._get_faster_whisper_model", side_effect=ImportError("no faster whisper")), \
         patch.dict(sys.modules, {"whisper": mock_openai_whisper}):
        srt = transcribe_audio("fake_audio.wav")
        assert "1\n00:00:01,000 --> 00:00:02,500\n来自openai-whisper转录" in srt


def test_transcribe_audio_raises_when_no_backend():
    with patch("scripts.whisper_transcribe._get_faster_whisper_model", side_effect=ImportError), \
         patch.dict(sys.modules, {"whisper": None}):
        with pytest.raises(RuntimeError, match="No Whisper transcription backend found"):
            transcribe_audio("fake_audio.wav")


def test_prepare_audio_source_handles_local_audio(tmp_path):
    fake_file = tmp_path / "test.mp3"
    fake_file.write_text("dummy")
    
    result_path = prepare_audio_source(str(fake_file), str(tmp_path))
    assert result_path == str(fake_file)
