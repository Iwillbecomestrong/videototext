"""Generate structured Markdown knowledge notes from technical video subtitles."""

import datetime
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


class MarkdownGenerator:
    """Generate structured Markdown engineering study notes."""

    def __init__(self, template_path: Optional[str] = "templates/note_template.md"):
        """Initialize with note template path."""
        self.template_path = Path(template_path) if template_path else None
        self.default_template = self._load_template()

    def _load_template(self) -> str:
        """Load template file content or fall back to default template."""
        if self.template_path and self.template_path.exists():
            return self.template_path.read_text(encoding="utf-8")

        return """# {{title}}

> **提取时间**：{{timestamp}}  
> **领域分类**：{{domain}}  
> **视频来源**：{{source}}

---

## 1. 核心概览 (Overview)
{{overview}}

---

## 2. 工具链与环境 (Toolchain & Environment)
{{toolchain}}

---

## 3. 关键配置与硬件参数 (Configurations & Parameters)
{{configurations}}

---

## 4. 核心原理解析 (Key Concepts & Principles)
{{principles}}

---

## 5. 开发流程与核心代码 (Workflow & Implementation)
{{workflow}}

---

## 6. 避坑指南与重点提醒 (Gotchas & Highlights)
{{highlights}}

---

## 7. 专业术语对照表 (Terminology Reference)
{{terminology}}
"""

    def extract_clean_text_from_srt(self, srt_content: str) -> str:
        """Strip SRT index and timestamp lines to return clean continuous text."""
        if not srt_content or not srt_content.strip():
            return ""

        timestamp_pattern = re.compile(
            r"^\d{1,2}:\d{2}:\d{2}[,\.]\d{3}\s*-->\s*\d{1,2}:\d{2}:\d{2}[,\.]\d{3}"
        )
        lines = srt_content.replace("\r\n", "\n").replace("\r", "\n").split("\n")

        text_lines = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.isdigit():
                continue
            if timestamp_pattern.search(stripped):
                continue
            text_lines.append(stripped)

        return "\n".join(text_lines)

    def generate_offline_summary(
        self,
        title: str,
        subtitle_text: str,
        domain: str = "motor-control",
        source: str = "",
        terms: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Generate structured markdown note offline without requiring an LLM API key."""
        clean_text = self.extract_clean_text_from_srt(subtitle_text)
        timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Extract paragraphs / bullet points from transcript
        paragraphs = [p for p in clean_text.split("\n") if p.strip()]
        overview_text = (
            "本笔记由视频字幕提取引擎自动整理生成。\n\n"
            + ("\n".join(paragraphs[:5]) if paragraphs else "暂无正文内容。")
        )

        # Detect toolchain terms
        detected_tools = set()
        detected_principles = set()
        common_tools = [
            "CubeMX",
            "Keil",
            "VS Code",
            "J-Link",
            "VOFA+",
            "MATLAB",
            "Simulink",
            "Git",
            "HAL库",
        ]
        common_principles = [
            "FOC",
            "SVPWM",
            "Clarke变换",
            "Park变换",
            "反Park",
            "PID",
            "PWM",
            "ADC",
            "马鞍波",
        ]

        full_content = clean_text + " " + " ".join([t.get("replacement", "") for t in (terms or [])])
        for tool in common_tools:
            if tool.lower() in full_content.lower():
                detected_tools.add(tool)

        for principle in common_principles:
            if principle.lower() in full_content.lower():
                detected_principles.add(principle)

        toolchain_md = (
            "\n".join([f"- **{t}**：课程演示或工程配置中涉及的关键开发工具" for t in sorted(detected_tools)])
            if detected_tools
            else "- 本课程使用标准嵌入式开发工具链。"
        )

        principles_md = (
            "\n".join([f"- **{p}**：核心控制算法与工程原理" for p in sorted(detected_principles)])
            if detected_principles
            else "- 请参考视频正文的理论讲解部分。"
        )

        configs_md = (
            "- **主控芯片/架构**：参考工程配置\n"
            "- **时钟与采样**：请结合具体代码与硬件原理图复核"
        )

        workflow_md = "1. 初始化开发环境与工程配置\n2. 编写核心算法驱动\n3. 在线联调与波形观测"
        highlights_md = "- 调试电机或功率板时注意安全限流，避免短路。"

        # Build terminology table
        if terms:
            term_rows = [
                "| 识别原词 | 纠错后标准术语 | 出现频次 |",
                "| :--- | :--- | :--- |",
            ]
            for t in sorted(terms, key=lambda x: x.get("count", 0), reverse=True):
                term_rows.append(
                    f"| `{t.get('original', '')}` | **{t.get('replacement', '')}** | {t.get('count', 1)} |"
                )
            terminology_md = "\n".join(term_rows)
        else:
            terminology_md = "未检测到特定纠错术语或字幕已非常标准。"

        rendered = self.default_template
        rendered = rendered.replace("{{title}}", title or "视频知识整理笔记")
        rendered = rendered.replace("{{timestamp}}", timestamp_str)
        rendered = rendered.replace("{{domain}}", domain)
        rendered = rendered.replace("{{source}}", source or "本地上传/未知链接")
        rendered = rendered.replace("{{overview}}", overview_text)
        rendered = rendered.replace("{{toolchain}}", toolchain_md)
        rendered = rendered.replace("{{configurations}}", configs_md)
        rendered = rendered.replace("{{principles}}", principles_md)
        rendered = rendered.replace("{{workflow}}", workflow_md)
        rendered = rendered.replace("{{highlights}}", highlights_md)
        rendered = rendered.replace("{{terminology}}", terminology_md)

        return rendered

    def generate_notes(
        self,
        subtitle_text: str,
        title: str,
        domain: str = "motor-control",
        source: str = "",
        terms: Optional[List[Dict[str, Any]]] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ) -> str:
        """Generate structured Markdown knowledge notes via LLM or rule-based fallback."""
        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            return self.generate_offline_summary(
                title=title,
                subtitle_text=subtitle_text,
                domain=domain,
                source=source,
                terms=terms,
            )

        url = base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        target_model = model or os.environ.get("OPENAI_MODEL", "gpt-4o")

        clean_transcript = self.extract_clean_text_from_srt(subtitle_text)
        # Limit transcript length if excessively long
        if len(clean_transcript) > 25000:
            clean_transcript = clean_transcript[:25000] + "\n...(以下字幕已截断)..."

        system_prompt = (
            "你是一个专业的技术视频知识提炼专家（擅长嵌入式、电机控制、算法与工程开发）。\n"
            "请根据用户提供的视频字幕和领域分类，生成一份结构极其严谨、排版精美、可直接用于复习和沉淀的工程技术学习笔记（Markdown 格式）。\n"
            "要求：\n"
            "1. 严格使用一级和二级标题，包含【核心概览】、【工具链与环境】、【关键配置与硬件参数】、【核心原理解析】、【开发流程与核心代码】、【避坑指南与重点提醒】、【专业术语表】。\n"
            "2. 语言凝练专业，技术专有名词严格使用标准大小写（如 FOC, CubeMX, VOFA+, STM32G431）。\n"
            "3. 只输出 Markdown 正文，不要包含外部思考标签或多余解释。"
        )

        user_content = (
            f"视频标题: {title}\n"
            f"领域: {domain}\n"
            f"来源: {source}\n\n"
            f"视频校正后字幕全文:\n{clean_transcript}\n"
        )

        try:
            import openai

            client = openai.OpenAI(api_key=key, base_url=url)
            response = client.chat.completions.create(
                model=target_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.3,
            )
            content = response.choices[0].message.content or ""
            return content.strip()
        except Exception as e:
            # Gracefully fallback to offline summary if LLM call fails
            fallback_note = self.generate_offline_summary(
                title=title,
                subtitle_text=subtitle_text,
                domain=domain,
                source=source,
                terms=terms,
            )
            warning_header = (
                f"> [!WARNING]\n"
                f"> 线上 LLM 接口调用失败 ({str(e)})，已自动切换为离线规则摘要生成。\n\n"
            )
            return warning_header + fallback_note
