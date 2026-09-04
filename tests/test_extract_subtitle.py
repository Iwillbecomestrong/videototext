import pytest
from scripts.extract_subtitle import vtt_to_srt, SubtitleResult


def test_vtt_to_srt_conversion():
    vtt_text = """WEBVTT
Kind: captions
Language: zh

00:00:01.200 --> 00:00:03.500 position:10%
欢迎来到本期视频

00:00:04.100 --> 00:00:07.800
<c>学习</c>电机控制算法
"""
    srt = vtt_to_srt(vtt_text)
    
    assert "1\n00:00:01,200 --> 00:00:03,500\n欢迎来到本期视频" in srt.replace("\r\n", "\n")
    assert "2\n00:00:04,100 --> 00:00:07,800\n学习电机控制算法" in srt.replace("\r\n", "\n")
    assert "WEBVTT" not in srt
    assert "<c>" not in srt
    assert "position:" not in srt


def test_vtt_to_srt_handles_already_indexed_vtt():
    vtt_text = """WEBVTT

1
00:01:05.000 --> 00:01:08.500
第一步：初始化系统时钟

2
00:01:09.000 --> 00:01:12.000
第二步：配置定时器通道
"""
    srt = vtt_to_srt(vtt_text)
    assert "1\n00:01:05,000 --> 00:01:08,500\n第一步：初始化系统时钟" in srt.replace("\r\n", "\n")
    assert "2\n00:01:09,000 --> 00:01:12,000\n第二步：配置定时器通道" in srt.replace("\r\n", "\n")


def test_subtitle_result_dataclass():
    res = SubtitleResult(
        has_subtitles=True,
        title="FOC教程",
        duration=120.5,
        subtitle_text="1\n00:00:01,000 --> 00:00:02,000\n测试",
        language="zh-Hans",
        source_url="https://example.com"
    )
    assert res.has_subtitles is True
    assert res.title == "FOC教程"
    assert "测试" in res.subtitle_text
