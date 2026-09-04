"""Audio and video downloader / extractor using yt-dlp and ffmpeg."""

import os
import re
import subprocess
from pathlib import Path
from typing import Optional


def is_url(source: str) -> bool:
    """Check if the source string is an HTTP/HTTPS URL."""
    return bool(re.match(r"^https?://", source.strip(), re.IGNORECASE))


def extract_audio_from_local_video(video_path: str, output_dir: str) -> str:
    """Extract 16kHz mono audio from a local video file using ffmpeg."""
    vpath = Path(video_path).resolve()
    if not vpath.exists():
        raise FileNotFoundError(f"Local video file not found: {video_path}")

    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    target_wav = out_dir / f"{vpath.stem}_audio.wav"

    if target_wav.exists() and target_wav.stat().st_size > 0:
        return str(target_wav)

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(vpath),
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        str(target_wav),
    ]

    try:
        subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return str(target_wav)
    except FileNotFoundError:
        raise RuntimeError(
            "ffmpeg is not installed or not in PATH. Please install ffmpeg to process local videos."
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"ffmpeg failed to extract audio: {e.stderr.decode(errors='replace')}")


def download_audio_from_url(url: str, output_dir: str) -> str:
    """Download audio stream from URL via yt-dlp."""
    try:
        import yt_dlp
    except ImportError:
        raise RuntimeError(
            "yt-dlp is not installed. Install with `pip install yt-dlp` to download audio."
        )

    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(out_dir / "%(id)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_id = info.get("id", "audio")
        target_wav = out_dir / f"{video_id}.wav"
        if target_wav.exists():
            return str(target_wav)
        # Check any matching audio files in output dir
        for f in out_dir.glob(f"{video_id}.*"):
            if f.suffix in [".wav", ".mp3", ".m4a", ".aac", ".opus"]:
                return str(f)
        raise RuntimeError(f"Downloaded audio file could not be located in {out_dir}")


def prepare_audio_source(source: str, output_dir: str = "./downloads") -> str:
    """Prepare an audio file path from either a URL or local file."""
    if is_url(source):
        return download_audio_from_url(source, output_dir)

    spath = Path(source)
    if not spath.exists():
        raise FileNotFoundError(f"Input file does not exist: {source}")

    audio_exts = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".opus"}
    if spath.suffix.lower() in audio_exts:
        return str(spath.resolve())

    # Treat as video file and extract audio
    return extract_audio_from_local_video(str(spath), output_dir)
