"""Extract online video subtitles and parse VTT/SRT/Bilibili formats."""

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
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
    provider: str = "generic"
    error: Optional[str] = None


def format_srt_timestamp(ts: str) -> str:
    """Format timestamp from mm:ss.xxx or hh:mm:ss.xxx to hh:mm:ss,xxx."""
    ts = ts.strip().replace(".", ",")
    parts = ts.split(":")
    if len(parts) == 2:
        return f"00:{parts[0].zfill(2)}:{parts[1]}"
    elif len(parts) == 3:
        return f"{parts[0].zfill(2)}:{parts[1].zfill(2)}:{parts[2]}"
    return ts


def format_seconds_to_srt(seconds: float) -> str:
    """Convert floating seconds to SRT timestamp HH:MM:SS,mmm."""
    if seconds < 0:
        seconds = 0.0
    total_ms = int(round(seconds * 1000))
    ms = total_ms % 1000
    total_sec = total_ms // 1000
    sec = total_sec % 60
    total_min = total_sec // 60
    minute = total_min % 60
    hour = total_min // 60
    return f"{hour:02d}:{minute:02d}:{sec:02d},{ms:03d}"


def bilibili_json_to_srt(data: Dict[str, Any]) -> str:
    """Convert Bilibili JSON subtitle data (with 'body' key) into standard SRT format."""
    body = data.get("body", [])
    if not body:
        return ""

    blocks = []
    for seq, item in enumerate(body, 1):
        from_sec = float(item.get("from", 0.0))
        to_sec = float(item.get("to", 0.0))
        content = str(item.get("content", "")).strip()
        if not content:
            continue

        start_ts = format_seconds_to_srt(from_sec)
        end_ts = format_seconds_to_srt(to_sec)
        block = f"{seq}\n{start_ts} --> {end_ts}\n{content}"
        blocks.append(block)

    return "\n\n".join(blocks) + "\n" if blocks else ""


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

        if (
            line.startswith("WEBVTT")
            or line.startswith("NOTE")
            or line.startswith("Kind:")
            or line.startswith("Language:")
        ):
            i += 1
            continue

        ts_match = timestamp_pattern.search(line)
        if ts_match:
            if current_timestamp and current_lines:
                text = "\n".join([l for l in current_lines if l])
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
                    text = "\n".join([l for l in current_lines if l])
                    blocks.append((current_timestamp, text))
                    current_timestamp = ""
                    current_lines = []
            else:
                cleaned_line = tag_pattern.sub("", line).strip()
                if not (cleaned_line.isdigit() and len(current_lines) == 0):
                    if cleaned_line:
                        current_lines.append(cleaned_line)
        i += 1

    if current_timestamp and current_lines:
        text = "\n".join([l for l in current_lines if l])
        blocks.append((current_timestamp, text))

    srt_blocks = []
    seq = 1
    for ts, text in blocks:
        if not text:
            continue
        srt_blocks.append(f"{seq}\n{ts}\n{text}")
        seq += 1

    return "\n\n".join(srt_blocks) + "\n" if srt_blocks else ""


def fetch_bilibili_native_subtitles(
    bvid: str, cookies: Optional[str] = None
) -> Optional[SubtitleResult]:
    """Fetch Bilibili subtitles directly via Bilibili Web API."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.bilibili.com",
        }
        if cookies:
            headers["Cookie"] = cookies

        # 1. Fetch video info to obtain cid and subtitle list
        info_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
        req = urllib.request.Request(info_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        if data.get("code") != 0 or "data" not in data:
            return None

        video_data = data["data"]
        title = video_data.get("title", "")
        duration = float(video_data.get("duration", 0.0))

        subtitle_info = video_data.get("subtitle", {})
        subtitles_list = subtitle_info.get("subtitles", [])

        if not subtitles_list:
            # Try player v2 endpoint if cid exists
            cid = video_data.get("cid")
            if cid:
                player_url = f"https://api.bilibili.com/x/player/v2?cid={cid}&bvid={bvid}"
                req_p = urllib.request.Request(player_url, headers=headers)
                with urllib.request.urlopen(req_p, timeout=10) as resp_p:
                    p_data = json.loads(resp_p.read().decode("utf-8"))
                    if p_data.get("code") == 0 and "data" in p_data:
                        subtitles_list = p_data["data"].get("subtitle", {}).get("subtitles", [])

        if not subtitles_list:
            return None

        # Pick first available subtitle (prefers zh-CN / ai-zh)
        chosen_sub = subtitles_list[0]
        for sub in subtitles_list:
            if "zh" in sub.get("lan", "") or "中文" in sub.get("lan_doc", ""):
                chosen_sub = sub
                break

        sub_url = chosen_sub.get("subtitle_url", "")
        if sub_url.startswith("//"):
            sub_url = "https:" + sub_url

        if not sub_url:
            return None

        sub_req = urllib.request.Request(sub_url, headers=headers)
        with urllib.request.urlopen(sub_req, timeout=10) as s_resp:
            sub_json = json.loads(s_resp.read().decode("utf-8"))

        srt_text = bilibili_json_to_srt(sub_json)
        if srt_text:
            return SubtitleResult(
                has_subtitles=True,
                title=title,
                duration=duration,
                subtitle_text=srt_text,
                language=chosen_sub.get("lan", "zh"),
                source_url=f"https://www.bilibili.com/video/{bvid}",
                provider="bilibili_native",
            )
    except Exception:
        return None

    return None


def fetch_online_subtitles(
    url: str,
    langs: Optional[List[str]] = None,
    cookies: Optional[str] = None,
) -> SubtitleResult:
    """Fetch online video subtitles (Bilibili native API / yt-dlp fallback)."""
    if langs is None:
        langs = ["ai-zh", "zh-Hans", "zh-CN", "zh", "en", "en-US"]

    is_bilibili = "bilibili.com" in url or "b23.tv" in url

    # Fast path: Bilibili Native API Provider
    if is_bilibili:
        bv_match = re.search(r"(BV[a-zA-Z0-9]{10})", url)
        if bv_match:
            bvid = bv_match.group(1)
            native_res = fetch_bilibili_native_subtitles(bvid, cookies=cookies)
            if native_res and native_res.has_subtitles:
                return native_res

    # General path: yt-dlp provider
    try:
        import yt_dlp
    except ImportError:
        return SubtitleResult(
            has_subtitles=False,
            source_url=url,
            error="yt-dlp is not installed. Run `pip install yt-dlp` to extract online subtitles.",
        )

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.bilibili.com",
    }
    if cookies and isinstance(cookies, str) and not (cookies.endswith(".txt")):
        headers["Cookie"] = cookies

    ydl_opts = {
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
        "http_headers": headers,
    }

    if cookies and isinstance(cookies, str) and (cookies.endswith(".txt") or "/" in cookies or "\\" in cookies):
        ydl_opts["cookiefile"] = cookies

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

            subtitles = info.get("subtitles") or {}
            auto_subs = info.get("automatic_captions") or {}

            chosen_url = None
            chosen_ext = "vtt"
            chosen_lang = None

            for lang in langs:
                for sub_dict in [subtitles, auto_subs]:
                    if lang in sub_dict and sub_dict[lang]:
                        formats = sub_dict[lang]
                        json_fmt = next((f for f in formats if f.get("ext") in ["json", "json3"]), None)
                        vtt_fmt = next((f for f in formats if f.get("ext") == "vtt"), None)
                        srt_fmt = next((f for f in formats if f.get("ext") == "srt"), None)
                        selected = json_fmt or vtt_fmt or srt_fmt or formats[0]
                        chosen_url = selected.get("url")
                        chosen_ext = selected.get("ext", "vtt")
                        chosen_lang = lang
                        break
                if chosen_url:
                    break

            if not chosen_url:
                hint = ""
                if is_bilibili:
                    hint = " (提示：部分B站视频字幕需登录，可配置 Cookie/SESSDATA 后重试，或自动降级为 Whisper 识别)"
                return SubtitleResult(
                    has_subtitles=False,
                    title=title,
                    duration=duration,
                    source_url=url,
                    provider="yt_dlp",
                    error=f"No official or auto-generated subtitle found in specified languages.{hint}",
                )

            headers = {"User-Agent": "Mozilla/5.0"}
            if cookies and isinstance(cookies, str) and not (cookies.endswith(".txt")):
                headers["Cookie"] = cookies

            req = urllib.request.Request(chosen_url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw_bytes = resp.read()

            try:
                content = raw_bytes.decode("utf-8")
            except UnicodeDecodeError:
                content = raw_bytes.decode("gbk", errors="replace")

            if chosen_ext in ["json", "json3"] or content.strip().startswith("{"):
                try:
                    data = json.loads(content)
                    srt_text = bilibili_json_to_srt(data)
                except Exception:
                    srt_text = vtt_to_srt(content)
            elif chosen_ext == "vtt" or "WEBVTT" in content:
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
                provider="yt_dlp",
            )

    except Exception as e:
        hint = ""
        if is_bilibili and ("login" in str(e).lower() or "403" in str(e) or "cookie" in str(e).lower()):
            hint = " (B站接口限制，请在 UI 或命令行传入 Cookie/SESSDATA，或直接使用 Whisper 离线转录)"
        return SubtitleResult(
            has_subtitles=False,
            source_url=url,
            provider="yt_dlp",
            error=f"Error extracting subtitle: {str(e)}{hint}",
        )
