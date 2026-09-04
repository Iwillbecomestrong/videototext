Markdown# Implementation Plan: video-knowledge-extractor

## 0. Planning Summary

目标：实现一个面向技术学习场景的视频知识提取 Skill 与工具系统。

核心输入：
- B站/YouTube 等视频 URL
- 本地音视频文件

核心输出：
1. 原始字幕 `xxx.srt`
2. 专业术语纠正字幕 `xxx_corrected.srt`
3. AI 结构化学习笔记 `xxx_notes.md`
4. 术语命中统计 `xxx_terms.json`

交付形态：
- AI Agent Skill (`SKILL.md`)
- CLI 工具
- Streamlit Web UI

MVP 范围严格遵循 SPEC：
- 包含字幕提取、ASR fallback、术语纠正、LLM 笔记生成、UI 展示。
- 不实现：
  - RAG
  - 向量数据库
  - 视频关键帧分析
  - 多用户系统
  - 云端部署


---

# 1. Architecture Overview

最终架构：

             User Input
                 |
    +------------+------------+
    |                         |
  URL Input              Local File
    |                         |
yt-dlp probe             ffmpeg
    |                         |
    +------------+------------+
                 |
         Subtitle Provider
                 |
    +------------+------------+
    |                         |
Official Subtitle            No Subtitle
|                         |
VTT/SRT Parse          Whisper ASR
|                         |
+------------+------------+
|
Raw Subtitle
(.srt)
|
SubtitleCleaner
|
+------------+------------+
|                         |
Corrected Subtitle        Term Report
|
MarkdownGenerator
|
Knowledge Notes
|
Output Directory

---

# 2. Implementation Order

## Phase 0: Project Foundation

### Goal

建立项目骨架、开发规范和基础运行环境。


## Files

Create:

README.md
AGENT_CORE.md
AGENTS.md
SKILL.md
requirements.txt
pyproject.toml
config/glossary.json
templates/note_template.md


## Tasks

### 1. Python package initialization

配置：

- Python >=3.10
- pytest
- streamlit
- yt-dlp
- faster-whisper
- openai compatible client


### 2. Output convention

统一：

output/
└── video_name/
├── raw.srt
├── corrected.srt
├── notes.md
└── terms.json


### Tests

新增：

tests/test_environment.py

验证：

- package import
- config loading


---

# Phase 1: Subtitle Extraction Module

## Objective

实现：

URL -> SubtitleResult


## Files

Create:

scripts/extract_subtitle.py
tests/test_extract_subtitle.py


## Interface


```python
@dataclass
class SubtitleResult:
    has_subtitles: bool
    title: str
    duration: float
    subtitle_text: str | None
    language: str | None
Function:
Python运行fetch_online_subtitles(
    url: str,
    langs=[
        "zh-Hans",
        "zh-CN",
        "zh",
        "en"
    ]
)->SubtitleResult
Implementation
使用：


yt-dlp metadata


yt-dlp subtitle extraction


处理：


VTT


SRT


UTF-8


UTF-8 BOM


GBK


转换：
WEBVTT

00:00:01.000 --> 00:00:03.000
text

↓

1
00:00:01,000 --> 00:00:03,000
text
Tests
覆盖：


VTT parsing


timestamp conversion


encoding handling


missing subtitle



Phase 2: Audio Download + Whisper ASR
Objective
无字幕视频自动转录。
Files
scripts/download_video.py
scripts/whisper_transcribe.py

tests/test_whisper_transcribe.py
Interfaces
download_video.py
Python运行download_audio(
    url:str,
    output_dir:str
)->str
流程：
URL
 |
yt-dlp
 |
audio stream
 |
wav/m4a
异常：


网络失败


视频不可访问


yt-dlp不存在


返回：
明确错误：
Install yt-dlp:

pip install yt-dlp

whisper_transcribe.py
接口：
Python运行transcribe_audio(
    audio_path:str,
    model_size="base",
    device="auto"
)->str
优先：
faster-whisper
Fallback:
openai-whisper
输出：
标准 SRT。
Tests
Mock:


Whisper result


missing dependency


避免 CI 下载模型。

Phase 3: Subtitle Cleaner
Objective
解决技术领域 ASR 错词。
Files
scripts/subtitle_cleaner.py
config/glossary.json

tests/test_subtitle_cleaner.py
Interface
Python运行class SubtitleCleaner:

    load_glossary()

    clean_text(
        text
    )->(
        cleaned,
        terms
    )

    clean_srt(
        srt
    )->(
        corrected_srt,
        terms
    )
Algorithm
顺序：


normalize lowercase


phrase matching


word matching


restore capitalization


Example:
Input:
今天学习 foo c 和 cubemix
Output:
今天学习 FOC 和 CubeMX
保持：
序号
时间戳
换行
不改变。
Tests
必须覆盖：


单词替换


短语替换


大小写


时间戳保护


多行字幕



Phase 4: Markdown Knowledge Generator
Objective
字幕 -> 工程学习笔记。
Files
scripts/markdown_generator.py
templates/note_template.md

tests/test_markdown_generator.py
Interface
Python运行class MarkdownGenerator:

    generate_notes(
        subtitle_text,
        title,
        domain="motor-control",
        api_key=None,
        base_url=None,
        model=None
    )->str
Template
生成：
Markdown# Title


## Overview


## Key Concepts


## Tools


## Configuration


## Code


## Summary
LLM
支持：


OpenAI compatible API


输入：
subtitle
+
template
输出：
markdown
Offline Mode
无 API：
返回：
规则摘要：
章节分割
关键词提取
术语列表
Tests
Mock:


LLM response


template rendering


missing key



Phase 5: Pipeline Integration
Objective
打通完整流程。
Files
scripts/pipeline.py
tests/test_pipeline.py
Interface
Python运行class KnowledgeExtractionPipeline:


    process(
        input_source,
        is_url,
        domain,
        output_dir
    )->PipelineResult
PipelineResult
Python运行@dataclass
class PipelineResult:

    raw_subtitle:str

    corrected_subtitle:str

    notes:str

    terms:str
Logic
if url:

    try official subtitle

    if fail:
        download audio
        whisper


else:

    extract audio
    whisper


then:

clean subtitle

generate notes

save files
Failure Strategy
允许：
字幕成功
+
AI失败

=> 保留字幕输出

Phase 6: Streamlit UI
Objective
提供可视化入口。
Files
ui/app.py
UI Layout
Video Knowledge Extractor


Input:

[ URL ]

or

[ Upload File ]


Domain:

[ motor-control ]


Start


-----------------

Raw Subtitle

Corrected Subtitle

Notes

Terms


Download buttons
Functions
支持：


输入 URL


上传文件


显示进度


查看结果


下载产物


启动：
Bashstreamlit run ui/app.py

Phase 7: Skill Integration
Objective
让 Agent 可以调用。
File
SKILL.md
内容：
定义：
name:
video-knowledge-extractor


trigger:

"When user provides video URL or asks for video notes"


workflow:

1 extract subtitle
2 clean terms
3 summarize
4 export markdown
兼容：


Claude


Gemini


Codex



3. Testing Strategy
Unit Tests
ModuleTestextract_subtitleVTT/SRTcleaner术语替换whispermockgeneratorLLM mockpipeline完整流程
Integration Test
模拟：
input.mp4

↓

raw.srt

↓

corrected.srt

↓

notes.md

↓

terms.json
禁止：
测试时真实下载大模型。

4. Risks
Risk 1: Whisper速度
问题：
CPU转录慢。
Mitigation:


默认base模型


支持cuda


支持tiny/small配置



Risk 2: B站字幕限制
问题：
字幕接口变化。
Mitigation:
封装：
SubtitleProvider
未来支持：


bilibili API


youtube API



Risk 3: LLM输出不稳定
Mitigation:
模板约束：
note_template.md
并支持：
dry-run

5. Verification Commands
Install
Bashpip install -r requirements.txt
Unit Test
Bashpytest tests
CLI
Example:
Bashpython -m scripts.pipeline \
--input URL \
--url
UI
Bashstreamlit run ui/app.py
Skill Check
Verify:
SKILL.md exists

Agent can discover skill

6. Suggested Commit Sequence
chore(repo): initialize video extractor project

feat(subtitle): implement subtitle extraction

feat(asr): add whisper transcription fallback

feat(cleaner): add technical glossary correction

feat(generator): add markdown knowledge generator

feat(core): integrate extraction pipeline

feat(ui): add streamlit interface

feat(skill): add agent skill definition

test(all): complete pipeline tests

7. Assumptions


默认 LLM 使用 OpenAI compatible API。


B站/YouTube字幕获取依赖第三方工具，不保证永久稳定。


UI 默认本地运行，不考虑部署。


专业词库初期人工维护，不自动学习。



8. SPEC Conflicts
未发现必须修改的 SPEC 冲突。
以下属于实现阶段可优化项，不改变需求：


可将字幕 Provider 抽象为接口，方便未来扩展。


可增加缓存机制减少重复转录。


可增加 CLI 参数系统。


以上不进入 M1 必做范围。
