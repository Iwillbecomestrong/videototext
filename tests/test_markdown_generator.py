from unittest.mock import MagicMock, patch
import pytest
from scripts.markdown_generator import MarkdownGenerator


def test_extract_clean_text_from_srt():
    gen = MarkdownGenerator()
    srt = """1
00:00:01,000 --> 00:00:03,000
欢迎学习 FOC 算法

2
00:00:04,000 --> 00:00:06,500
接下来打开 CubeMX 进行配置
"""
    clean_text = gen.extract_clean_text_from_srt(srt)
    assert "欢迎学习 FOC 算法" in clean_text
    assert "接下来打开 CubeMX 进行配置" in clean_text
    assert "00:00:01,000" not in clean_text
    assert "1\n" not in clean_text


def test_generate_mock_mode_produces_structured_engineering_notes():
    gen = MarkdownGenerator()
    srt = """1
00:00:01,000 --> 00:00:03,000
本节课讲 STM32G431 的 FOC 驱动开发，使用 CubeMX 和 Keil uVision
"""
    terms = [
        {"original": "foo c", "replacement": "FOC", "count": 2},
        {"original": "cooper mix", "replacement": "CubeMX", "count": 1}
    ]
    notes = gen.generate_notes(
        subtitle_text=srt,
        title="STM32 FOC实战课程",
        domain="motor-control",
        source="https://www.bilibili.com/video/BV123",
        terms=terms,
        mock=True
    )
    
    assert "# STM32 FOC实战课程" in notes
    assert "核心概览" in notes or "Overview" in notes
    assert "工具链与环境" in notes or "Toolchain" in notes
    assert "核心原理解析" in notes or "Principles" in notes
    assert "CubeMX" in notes
    assert "FOC" in notes
    assert "专业术语对照表" in notes or "Terminology" in notes


def test_generate_offline_summary_fills_template():
    gen = MarkdownGenerator()
    srt = """1
00:00:01,000 --> 00:00:03,000
本节课讲 STM32G431 的 FOC 驱动开发，使用 CubeMX 和 Keil uVision
"""
    terms = [
        {"original": "foo c", "replacement": "FOC", "count": 2},
        {"original": "cooper mix", "replacement": "CubeMX", "count": 1}
    ]
    notes = gen.generate_offline_summary(
        title="STM32 FOC实战",
        subtitle_text=srt,
        domain="motor-control",
        source="https://bilibili.com/video/BV123",
        terms=terms
    )
    
    assert "# STM32 FOC实战" in notes
    assert "motor-control" in notes
    assert "CubeMX" in notes
    assert "FOC" in notes


def test_generate_notes_calls_openai_when_key_present():
    gen = MarkdownGenerator()
    fake_completion = MagicMock()
    fake_completion.choices = [
        MagicMock(message=MagicMock(content="# AI 生成的 FOC 核心笔记\n\n## 1. 核心概览\n原理详解"))
    ]
    
    with patch("openai.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = fake_completion
        mock_openai_cls.return_value = mock_client
        
        result = gen.generate_notes(
            subtitle_text="1\n00:00:01,000 --> 00:00:03,000\nFOC算法内容",
            title="测试课程",
            api_key="sk-fake-key",
            model="gpt-4o"
        )
        assert "# AI 生成的 FOC 核心笔记" in result
        mock_client.chat.completions.create.assert_called_once()
