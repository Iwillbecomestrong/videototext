"""Extract online video subtitles and parse VTT/SRT formats."""

import re
from dataclasses import dataclass
from typing import List, Optional
import urllib.request


@dataclass
class SubtitleResult:
    """Dataclass holding extracted subtitle details."""

    has_subtitles: bool
    title: str = ""
    duration: float = 0.0
    subtitle_text: Optional[str] = None
    language: Optional[str] = None
    source_url: str = ""
    error: Optional[str] = None


def format_srt_timestamp(ts: str) -> str:
    """Format timestamp from mm:ss.xxx or hh:mm:ss.xxx to hh:mm:ss,xxx."""
    ts = ts.strip().replace(".", ",")
    parts = ts.split(":")
    if len(parts) == 2:
        # mm:ss,xxx -> 00:mm:ss,xxx
        return f"00:{parts[0].zfill(2)}:{parts[1]}"
    elif len(parts) == 3:
        # hh:mm:ss,xxx -> hh(2):mm(2):ss,xxx
        return f"{parts[0].zfill(2)}:{parts[1].zfill(2)}:{parts[2]}"
    return ts


def vtt_to_srt(vtt_content: str) -> str:
    """Convert WebVTT formatted subtitles into standard SubRip (SRT) format."""
    if not vtt_content or not vtt_content.strip():
        return ""

    lines = vtt_content.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    
    timestamp_pattern = re.compile(
        r"((?:\d{1,2}:)?\d{2}:\d{2}[\.,]\d{3})\s*-->\s*((?:\d{1,2}:)?\d{2}:\d{2}[\.,]\d{3})"
    )
    tag_pattern = re.compile(r"<[^>]+>|\{[^}]+\}")

    blocks = []
    current_timestamp = ""
    current_lines: List[str] = []
    
    i = 0
    total = len(lines)
    while i < total:
        line = lines[i].strip()
        
        # Skip WebVTT header and styling notes
        if line.startswith("WEBVTT") or line.startswith("NOTE") or line.startswith("Kind:") or line.startswith("Language:"):
            i += 1
            continue
            
        ts_match = timestamp_pattern.search(line)
        if ts_match:
            # If we had a previous block, record it
            if current_timestamp and current_lines:
                text = " ".join([l for l in current_lines if l])
                blocks.append((current_timestamp, text))
                current_lines = []
                
            start_ts = format_srt_timestamp(ts_match.group(1))
            end_ts = format_srt_timestamp(ts_match.group(2))
            current_timestamp = f"{start_ts} --> {end_ts}"
            i += 1
            continue
            
        if current_timestamp:
            if not line:
                if current_lines:
                    text = " ".join([l for l in current_lines if l])
                    blocks.append((current_timestamp, text))
                    current_timestamp = ""
                    current_lines = []
            else:
                # Clean tags and styling from text
                cleaned_line = tag_pattern.sub("", line).strip()
                # Ignore isolated numeric index lines in source VTT
                if not (cleaned_line.isdigit() and len(current_lines) == 0):
                    if cleaned_line:
                        current_lines.append(cleaned_line)
        i += 1
        
    if current_timestamp and current_lines:
        text = " ".join([l for l in current_lines if l])
        blocks.append((current_timestamp, text))

    # Build standard numbered SRT blocks, de-duplicating adjacent identical text
    srt_blocks = []
    seq = 1
    last_text = ""
    for ts, text in blocks:
        if not text:
            continue
        if text == last_text and srt_blocks:
            continue
        srt_blocks.append(f"{seq}\n{ts}\n{text}")
        last_text = text
        seq += 1

    return "\n\n".join(srt_blocks) + "\n" if srt_blocks else ""


def fetch_online_subtitles(
    url: str, langs: Optional[List[str]] = None
) -> SubtitleResult:
    """Fetch online video subtitles using yt-dlp if available."""
    if langs is None:
        langs = ["zh-Hans", "zh-CN", "zh", "en", "en-US"]

    try:
        import yt_dlp
    except ImportError:
        return SubtitleResult(
            has_subtitles=False,
            source_url=url,
            error="yt-dlp is not installed. Run `pip install yt-dlp` to extract online subtitles.",
        )

    ydl_opts = {
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                return SubtitleResult(
                    has_subtitles=False,
                    source_url=url,
                    error="Failed to extract video info.",
                )

            title = info.get("title", "Unknown Title")
            duration = float(info.get("duration") or 0.0)

            # Look for requested language subtitles: official first, then automatic
            subtitles = info.get("subtitles") or {}
            auto_subs = info.get("automatic_captions") or {}

            chosen_url = None
            chosen_ext = "vtt"
            chosen_lang = None

            for lang in langs:
                for sub_dict in [subtitles, auto_subs]:
                    if lang in sub_dict and sub_dict[lang]:
                        formats = sub_dict[lang]
                        # Prefer vtt or srt
                        vtt_fmt = next((f for f in formats if f.get("ext") == "vtt"), None)
                        srt_fmt = next((f for f in formats if f.get("ext") == "srt"), None)
                        selected = vtt_fmt or srt_fmt or formats[0]
                        chosen_url = selected.get("url")
                        chosen_ext = selected.get("ext", "vtt")
                        chosen_lang = lang
                        break
                if chosen_url:
                    break

            if not chosen_url:
                return SubtitleResult(
                    has_subtitles=False,
                    title=title,
                    duration=duration,
                    source_url=url,
                    error="No official or auto-generated subtitle found in specified languages.",
                )

            # Fetch the subtitle content
            req = urllib.request.Request(
                chosen_url, headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                content = resp.read().decode("utf-8", errors="replace")

            if chosen_ext == "vtt" or "WEBVTT" in content:
                srt_text = vtt_to_srt(content)
            else:
                srt_text = content

            return SubtitleResult(
                has_subtitles=True,
                title=title,
                duration=duration,
                subtitle_text=srt_text,
                language=chosen_lang,
                source_url=url,
            )

    except Exception as e:
        return SubtitleResult(
            has_subtitles=False,
            source_url=url,
            error=f"Error extracting subtitle: {str(e)}",
        )
