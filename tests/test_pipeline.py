from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from scripts.pipeline import KnowledgeExtractionPipeline, PipelineResult
from scripts.extract_subtitle import SubtitleResult


def test_pipeline_with_mocked_online_subtitle(tmp_path):
    pipeline = KnowledgeExtractionPipeline(output_base_dir=str(tmp_path), domain="motor-control")
    
    mock_sub_result = SubtitleResult(
        has_subtitles=True,
        title="STM32G431 FOC入门教程",
        duration=300.0,
        subtitle_text="""1
00:00:01,000 --> 00:00:04,000
欢迎学习 foo c 课程，使用 cooper mix 进行配置。
""",
        language="zh-Hans",
        source_url="https://www.bilibili.com/video/BV123456"
    )
    
    with patch("scripts.pipeline.fetch_online_subtitles", return_value=mock_sub_result):
        result = pipeline.process("https://www.bilibili.com/video/BV123456")
        
        assert isinstance(result, PipelineResult)
        assert result.title == "STM32G431 FOC入门教程"
        assert Path(result.raw_srt_path).exists()
        assert Path(result.corrected_srt_path).exists()
        assert Path(result.notes_md_path).exists()
        assert Path(result.terms_json_path).exists()
        
        # Verify corrected srt content
        corrected_content = Path(result.corrected_srt_path).read_text(encoding="utf-8")
        assert "FOC" in corrected_content
        assert "CubeMX" in corrected_content
        assert "foo c" not in corrected_content
        
        # Verify markdown notes content
        notes_content = Path(result.notes_md_path).read_text(encoding="utf-8")
        assert "STM32G431 FOC入门教程" in notes_content
        assert "FOC" in notes_content


def test_pipeline_fallback_to_whisper_when_no_subtitles(tmp_path):
    pipeline = KnowledgeExtractionPipeline(output_base_dir=str(tmp_path), domain="motor-control")
    
    no_sub_result = SubtitleResult(
        has_subtitles=False,
        title="无字幕视频",
        source_url="https://example.com/no-sub"
    )
    
    with patch("scripts.pipeline.fetch_online_subtitles", return_value=no_sub_result), \
         patch("scripts.pipeline.prepare_audio_source", return_value="fake_audio.wav"), \
         patch("scripts.pipeline.transcribe_audio", return_value="1\n00:00:01,000 --> 00:00:03,000\n测试转写 foo c"):
        
        result = pipeline.process("https://example.com/no-sub")
        assert result.title == "无字幕视频"
        assert Path(result.corrected_srt_path).exists()
        assert "FOC" in Path(result.corrected_srt_path).read_text(encoding="utf-8")
