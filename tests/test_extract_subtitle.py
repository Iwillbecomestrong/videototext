import json
import pytest
from scripts.extract_subtitle import vtt_to_srt, bilibili_json_to_srt, SubtitleResult, fetch_online_subtitles


def test_vtt_to_srt_preserves_multiline_text():
    vtt_text = """WEBVTT

00:00:01.200 --> 00:00:03.500
第一行说明
第二行补充说明
"""
    srt = vtt_to_srt(vtt_text)
    assert "1\n00:00:01,200 --> 00:00:03,500\n第一行说明\n第二行补充说明" in srt.replace("\r\n", "\n")


def test_bilibili_json_to_srt_conversion():
    bili_data = {
        "body": [
            {"from": 1.5, "to": 3.8, "content": "欢迎观看B站电机教程"},
            {"from": 4.0, "to": 7.2, "content": "本期讲解Clarke变换与Park变换"}
        ]
    }
    srt = bilibili_json_to_srt(bili_data)
    assert "1\n00:00:01,500 --> 00:00:03,800\n欢迎观看B站电机教程" in srt
    assert "2\n00:00:04,000 --> 00:00:07,200\n本期讲解Clarke变换与Park变换" in srt


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
