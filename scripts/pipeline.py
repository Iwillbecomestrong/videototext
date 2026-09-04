"""End-to-end video knowledge extraction pipeline orchestrator."""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from scripts.download_video import is_url, prepare_audio_source
from scripts.extract_subtitle import fetch_online_subtitles
from scripts.markdown_generator import MarkdownGenerator
from scripts.subtitle_cleaner import SubtitleCleaner
from scripts.whisper_transcribe import transcribe_audio


@dataclass
class PipelineResult:
    """Dataclass holding all artifact paths produced by the pipeline."""

    title: str
    raw_srt_path: str
    corrected_srt_path: str
    notes_md_path: str
    terms_json_path: str
    terms_count: int
    source: str
    output_dir: str
    error: Optional[str] = None


def sanitize_filename(name: str) -> str:
    """Sanitize string to be safe for filesystem paths across Windows/Linux."""
    cleaned = re.sub(r'[\\/*?:"<>|]', "_", name).strip()
    cleaned = re.sub(r"\s+", "_", cleaned)
    return cleaned[:80] if cleaned else "video_knowledge"


class KnowledgeExtractionPipeline:
    """Unified pipeline connecting subtitle extraction, glossary cleaner, and note generation."""

    def __init__(
        self,
        output_base_dir: str = "./output",
        domain: str = "motor-control",
        glossary_path: Optional[str] = "config/glossary.json",
        template_path: Optional[str] = "templates/note_template.md",
    ):
        self.output_base_dir = Path(output_base_dir)
        self.domain = domain
        self.glossary_path = glossary_path
        self.cleaner = SubtitleCleaner(glossary=glossary_path, domain=domain)
        self.generator = MarkdownGenerator(template_path=template_path)

    def process(
        self,
        input_source: str,
        domain: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        force_whisper: bool = False,
        cookies: Optional[str] = None,
        mock: bool = False,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> PipelineResult:
        """Execute extraction pipeline on URL or local file."""
        target_domain = domain or self.domain
        if target_domain != self.domain:
            self.cleaner = SubtitleCleaner(
                glossary=self.glossary_path, domain=target_domain
            )

        source_is_url = is_url(input_source)
        title = ""
        raw_srt = ""

        # Step 1: Subtitle acquisition
        if progress_callback:
            progress_callback("正在检测视频字幕...", 0.1)

        sub_result = None
        if source_is_url and not force_whisper:
            try:
                sub_result = fetch_online_subtitles(input_source, cookies=cookies)
                if sub_result and sub_result.has_subtitles and sub_result.subtitle_text:
                    raw_srt = sub_result.subtitle_text
                    title = sub_result.title
            except Exception:
                sub_result = None

        if not raw_srt:
            # Fallback to audio extraction + Whisper ASR
            if progress_callback:
                progress_callback("未检测到原生字幕，正在准备音频进行语音识别...", 0.3)

            downloads_dir = self.output_base_dir / "downloads"
            downloads_dir.mkdir(parents=True, exist_ok=True)

            try:
                audio_path = prepare_audio_source(
                    input_source, str(downloads_dir), cookies=cookies
                )
                if not title:
                    if sub_result and sub_result.title:
                        title = sub_result.title
                    else:
                        title = Path(input_source).stem

                if progress_callback:
                    progress_callback("正在使用 Whisper 进行语音转写...", 0.5)

                domain_prompts = {
                    "motor-control": (
                        "这是一段关于电机控制与控制理论的视频教程，涉及传递函数、低通滤波器、"
                        "截止频率omega_c、正弦信号、幅值、相位、比例积分微分PID、"
                        "S域到Z域离散化、差分方程、采样周期Ts、STM32单片机FOC实现。"
                    ),
                    "general-tech": "这是一段技术开发教程，包含编程、算法、系统架构与工程实战讲解。",
                }
                whisper_prompt = domain_prompts.get(target_domain, None)
                raw_srt = transcribe_audio(audio_path, initial_prompt=whisper_prompt)
            except Exception as e:
                # If in mock mode (e.g. user entered a dummy test URL like BV123456 or offline demo),
                # provide rich simulated sample subtitles instead of crashing.
                if mock:
                    if progress_callback:
                        progress_callback("检测到 Mock 演示模式，自动加载电机实战模拟教学字幕...", 0.5)
                    title = "STM32G431_FOC算法实战教程_演示"
                    raw_srt = (
                        "1\n00:00:01,000 --> 00:00:04,500\n"
                        "欢迎来到 foo c 驱动开发教程，今天配合 cooper mix 进行底层配置。\n\n"
                        "2\n00:00:05,000 --> 00:00:09,200\n"
                        "我们将使用 stm 32 主控，通过 无法加 上位机实时观测马鞍波和 sv pwm 波形。\n\n"
                        "3\n00:00:10,000 --> 00:00:14,000\n"
                        "核心算法包括 clark变换 和 park变换，并利用 p i 调节器实现电流环闭环控制。\n"
                    )
                else:
                    raise RuntimeError(
                        f"无法获取视频音频或转录字幕 ({str(e)})。"
                        "如果视频链接为演示假链接，可添加 `--mock` 参数进行体验；"
                        "若是真实链接，请检查网络连接或是否需要配置 B站 Cookie。"
                    )

        if not title:
            title = "Video_Knowledge"

        # Step 2: Terminology correction
        if progress_callback:
            progress_callback(f"正在进行领域术语校正 [{target_domain}]...", 0.7)

        corrected_srt, terms = self.cleaner.clean_srt(raw_srt)

        # Step 3: Markdown knowledge notes generation
        if progress_callback:
            progress_callback("正在整理结构化工程学习笔记...", 0.85)

        notes_md = self.generator.generate_notes(
            subtitle_text=corrected_srt,
            title=title,
            domain=target_domain,
            source=input_source,
            terms=terms,
            api_key=api_key,
            base_url=base_url,
            model=model,
            mock=mock,
        )

        # Step 4: Persist all artifacts
        safe_title = sanitize_filename(title)
        video_out_dir = self.output_base_dir / safe_title
        video_out_dir.mkdir(parents=True, exist_ok=True)

        raw_srt_path = video_out_dir / f"{safe_title}_raw.srt"
        corrected_srt_path = video_out_dir / f"{safe_title}_corrected.srt"
        notes_md_path = video_out_dir / f"{safe_title}_notes.md"
        terms_json_path = video_out_dir / f"{safe_title}_terms.json"

        raw_srt_path.write_text(raw_srt, encoding="utf-8")
        corrected_srt_path.write_text(corrected_srt, encoding="utf-8")
        notes_md_path.write_text(notes_md, encoding="utf-8")

        with open(terms_json_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "title": title,
                    "domain": target_domain,
                    "source": input_source,
                    "terms": terms,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        if progress_callback:
            progress_callback("全部任务处理完成！", 1.0)

        total_terms_count = sum(t.get("count", 0) for t in terms)

        return PipelineResult(
            title=title,
            raw_srt_path=str(raw_srt_path),
            corrected_srt_path=str(corrected_srt_path),
            notes_md_path=str(notes_md_path),
            terms_json_path=str(terms_json_path),
            terms_count=total_terms_count,
            source=input_source,
            output_dir=str(video_out_dir),
        )


def main():
    """CLI entry point for video knowledge extractor pipeline."""
    parser = argparse.ArgumentParser(
        description="Video Knowledge Extractor: Extract subtitles, correct domain terms, generate notes."
    )
    parser.add_argument("source", help="Video URL (Bilibili/YouTube) or path to local video/audio file")
    parser.add_argument("--domain", default="motor-control", help="Domain glossary (motor-control, general-tech)")
    parser.add_argument("--output", default="./output", help="Output directory")
    parser.add_argument("--api-key", default=None, help="OpenAI-compatible API key")
    parser.add_argument("--base-url", default=None, help="OpenAI-compatible Base URL")
    parser.add_argument("--model", default=None, help="Model name (e.g. gpt-4o, deepseek-chat)")
    parser.add_argument("--force-whisper", action="store_true", help="Force Whisper transcription instead of online subtitles")
    parser.add_argument("--cookies", default=None, help="Cookie string or path to cookies.txt for Bilibili/YouTube")
    parser.add_argument("--mock", action="store_true", help="Enable high-fidelity Mock LLM mode for testing/demo")

    args = parser.parse_args()

    pipeline = KnowledgeExtractionPipeline(output_base_dir=args.output, domain=args.domain)
    print(f"[+] Starting extraction for: {args.source}")
    result = pipeline.process(
        input_source=args.source,
        domain=args.domain,
        api_key=args.api_key,
        base_url=args.base_url,
        model=args.model,
        force_whisper=args.force_whisper,
        cookies=args.cookies,
        mock=args.mock,
        progress_callback=lambda msg, progress: print(f"[{int(progress*100)}%] {msg}"),
    )

    print("\n[+] 知识提取完成!")
    print(f"  - 视频标题: {result.title}")
    print(f"  - 原始字幕: {result.raw_srt_path}")
    print(f"  - 校正字幕: {result.corrected_srt_path}")
    print(f"  - 学习笔记: {result.notes_md_path}")
    print(f"  - 术语统计: {result.terms_json_path} (匹配 {result.terms_count} 处)")


if __name__ == "__main__":
    main()
