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


def download_audio_from_url(url: str, output_dir: str, cookies: Optional[str] = None) -> str:
    """Download audio stream from URL via yt-dlp with anti-bot headers."""
    try:
        import yt_dlp
    except ImportError:
        raise RuntimeError(
            "yt-dlp is not installed. Install with `pip install yt-dlp` to download audio."
        )

    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(out_dir / "%(id)s.%(ext)s")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.bilibili.com",
    }
    if cookies and isinstance(cookies, str) and not (cookies.endswith(".txt")):
        headers["Cookie"] = cookies

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "http_headers": headers,
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

    if cookies and isinstance(cookies, str) and (cookies.endswith(".txt") or "/" in cookies or "\\" in cookies):
        ydl_opts["cookiefile"] = cookies

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_id = info.get("id", "audio")
            target_wav = out_dir / f"{video_id}.wav"
            if target_wav.exists():
                return str(target_wav)
            for f in out_dir.glob(f"{video_id}.*"):
                if f.suffix in [".wav", ".mp3", ".m4a", ".aac", ".opus"]:
                    return str(f)
            raise RuntimeError(f"Downloaded audio file could not be located in {out_dir}")
    except Exception as e:
        raise RuntimeError(f"音频下载失败 ({str(e)})。如果该视频受权限保护，请提供 B站 Cookie。")


def prepare_audio_source(
    source: str, output_dir: str = "./downloads", cookies: Optional[str] = None
) -> str:
    """Prepare an audio file path from either a URL or local file."""
    if is_url(source):
        return download_audio_from_url(source, output_dir, cookies=cookies)

    spath = Path(source)
    if not spath.exists():
        raise FileNotFoundError(f"Input file does not exist: {source}")

    audio_exts = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".opus"}
    if spath.suffix.lower() in audio_exts:
        return str(spath.resolve())

    # Treat as video file and extract audio
    return extract_audio_from_local_video(str(spath), output_dir)
