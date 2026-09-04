"""Whisper ASR transcription module supporting faster-whisper and openai-whisper."""

import math
from typing import Any, Iterable, List, Optional


def format_seconds_to_srt_timestamp(seconds: float) -> str:
    """Convert floating-point seconds into SRT timestamp format HH:MM:SS,mmm."""
    if seconds < 0:
        seconds = 0.0

    total_ms = int(round(seconds * 1000))
    ms = total_ms % 1000
    total_seconds = total_ms // 1000
    sec = total_seconds % 60
    total_minutes = total_seconds // 60
    minute = total_minutes % 60
    hour = total_minutes // 60

    return f"{hour:02d}:{minute:02d}:{sec:02d},{ms:03d}"


def segments_to_srt(segments: Iterable[Any]) -> str:
    """Format segments with .start, .end, and .text into standard numbered SRT."""
    blocks: List[str] = []
    seq = 1

    for seg in segments:
        text = getattr(seg, "text", "").strip()
        if not text:
            continue

        start_ts = format_seconds_to_srt_timestamp(getattr(seg, "start", 0.0))
        end_ts = format_seconds_to_srt_timestamp(getattr(seg, "end", 0.0))

        block = f"{seq}\n{start_ts} --> {end_ts}\n{text}"
        blocks.append(block)
        seq += 1

    return "\n\n".join(blocks) + "\n" if blocks else ""


def _get_faster_whisper_model(
    model_size: str = "base", device: str = "auto", compute_type: str = "auto"
):
    """Factory helper to obtain a faster_whisper WhisperModel instance."""
    import os
    if "HF_HUB_DISABLE_SYMLINKS_WARNING" not in os.environ:
        os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
    from faster_whisper import WhisperModel

    local_candidates = [
        os.path.join("models", f"faster-whisper-{model_size}"),
        os.path.join("models", model_size),
    ]
    model_path = model_size
    for cand in local_candidates:
        if os.path.isdir(cand) and os.path.exists(os.path.join(cand, "model.bin")):
            model_path = cand
            break

    try:
        return WhisperModel(model_path, device=device, compute_type=compute_type)
    except RuntimeError as e:
        if "cublas" in str(e).lower() or device != "cpu":
            # Graceful fallback to CPU if CUDA library is missing
            return WhisperModel(model_path, device="cpu", compute_type="int8")
        raise


def transcribe_audio(
    audio_path: str,
    model_size: str = "base",
    device: str = "auto",
    language: Optional[str] = "zh",
    initial_prompt: Optional[str] = None,
) -> str:
    """Transcribe an audio file to SRT using faster-whisper or openai-whisper."""
    # 1. Try faster-whisper
    try:
        model = _get_faster_whisper_model(model_size, device=device)
        transcribe_kwargs = {}
        if language:
            transcribe_kwargs["language"] = language
        if initial_prompt:
            transcribe_kwargs["initial_prompt"] = initial_prompt

        try:
            segments, info = model.transcribe(audio_path, **transcribe_kwargs)
            return segments_to_srt(segments)
        except RuntimeError as e:
            if "cublas" in str(e).lower():
                from faster_whisper import WhisperModel
                local_candidates = [
                    os.path.join("models", f"faster-whisper-{model_size}"),
                    os.path.join("models", model_size),
                ]
                model_path = model_size
                for cand in local_candidates:
                    if os.path.isdir(cand) and os.path.exists(os.path.join(cand, "model.bin")):
                        model_path = cand
                        break
                cpu_model = WhisperModel(model_path, device="cpu", compute_type="int8")
                segments, info = cpu_model.transcribe(audio_path, **transcribe_kwargs)
                return segments_to_srt(segments)
            raise
    except (ImportError, ModuleNotFoundError):
        pass

    # 2. Try standard openai-whisper fallback
    try:
        import whisper

        model = whisper.load_model(model_size)
        transcribe_kwargs = {}
        if language:
            transcribe_kwargs["language"] = language
        if initial_prompt:
            transcribe_kwargs["initial_prompt"] = initial_prompt

        result = model.transcribe(audio_path, **transcribe_kwargs)
        raw_segments = result.get("segments", [])

        # Adapt dictionary segments
        class DictSegment:
            def __init__(self, d):
                self.start = d.get("start", 0.0)
                self.end = d.get("end", 0.0)
                self.text = d.get("text", "")

        adapted = [DictSegment(s) for s in raw_segments]
        return segments_to_srt(adapted)
    except (ImportError, ModuleNotFoundError):
        pass

    raise RuntimeError(
        "No Whisper transcription backend found. "
        "Please install faster-whisper (`pip install faster-whisper`) "
        "or openai-whisper (`pip install -U openai-whisper`)."
    )
