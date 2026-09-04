# Web GPT Review Report (Target Commit: eb9175d)

- **Repository**: Iwillbecomestrong/videototext
- **Base Commit**: 2f77ce6
- **Target Commit**: eb9175d
- **SPEC**: docs/specs/video-knowledge-extractor.md
- **Status**: SUCCESS
- **Attestation**: Repo=YES, Commit=YES, Spec=YES, Base=YES

## Web GPT Review Findings

```text
REPOSITORY_VERIFIED: YES
BASE_COMMIT_VERIFIED: YES
TARGET_COMMIT_VERIFIED: YES
SPEC_VERIFIED: YES
REPOSITORY: Iwillbecomestrong/videototext
BASE_COMMIT: 2f77ce6
TARGET_COMMIT: eb9175d
SPEC: docs/specs/video-knowledge-extractor.md
FILES_INSPECTED:
docs/specs/video-knowledge-extractor.md
scripts/pipeline.py
scripts/extract_subtitle.py
scripts/markdown_generator.py
ui/app.py
scripts/subtitle_cleaner.py
scripts/whisper_transcribe.py
tests/test_pipeline.py
tests/test_extract_subtitle.py
tests/test_markdown_generator.py
tests/test_subtitle_cleaner.py

Findings

Severity: MAJOR
File: scripts/pipeline.py, scripts/markdown_generator.py
Location: KnowledgeExtractionPipeline.process() → Step 3 Markdown generation
Evidence: SPEC 要求 markdown_generator.py 支持基于 templates/note_template.md + LLM 生成结构化笔记，并支持 Dry-Run / Mock 模式。当前实现虽然提供了 LLM 调用和离线 fallback，但离线模式只是规则拼接摘要，不是真正的结构化知识提炼；同时 pipeline 默认在无 API Key 时直接进入离线摘要路径。
Reason: MVP 可运行，但对于 SPEC 中“AI 结构化总结（工具链、配置参数、核心原理与代码/步骤）”这一核心能力，离线 fallback 不能完全替代 Mock/LLM 生成能力。最终产物可能只是字幕摘要，而不是知识笔记。
Recommended Fix: 增加明确的 Mock LLM 模式（例如 mock=True 或环境变量 MOCK_LLM=1），生成稳定测试用 Markdown；区分“无 API 的 demo 模式”和“生产知识提取模式”。

Severity: MAJOR
File: scripts/extract_subtitle.py
Location: fetch_online_subtitles()
Evidence: SPEC 要求支持“B站/YouTube 等视频链接”，并要求优先抓取官方 CC/字幕。当前实现依赖 yt_dlp 获取字幕信息，但未针对 Bilibili 特殊字幕格式、登录限制、cookie、弹幕字幕等情况处理。
Reason: 对常见 YouTube 场景可工作，但目标用户主要是技术学习视频，B站是重要输入源。当前实现可能大量进入 Whisper fallback，导致性能和体验下降。
Recommended Fix: 增加 Bilibili provider 层；至少检测 B站字幕接口失败原因，并在错误信息中提示 cookie/session 配置方式，支持 cookies 传入。

Severity: MAJOR
File: scripts/whisper_transcribe.py
Location: transcribe_audio()
Evidence: SPEC 明确要求优先调用 faster_whisper.WhisperModel，如果环境不满足再兼容 openai-whisper 或给出清晰错误。需要验证实际实现是否满足该接口和 fallback 逻辑。
Reason: ASR 是无字幕情况下的关键链路，如果 faster-whisper fallback 不完整，会导致核心能力失效。
Recommended Fix: 补充实现审查和测试：faster-whisper 可用路径；openai-whisper fallback；缺少依赖时的明确错误；输出 SRT 格式验证。

Severity: MINOR
File: scripts/extract_subtitle.py
Location: vtt_to_srt()
Evidence: 当前转换逻辑会把多行字幕合并为单行文本，并对连续完全相同字幕块去重。
Reason: 对普通字幕有效，但可能改变原字幕语义和换行结构，不完全符合“仅修正正文，保持 SRT 序号与时间轴”的约束。
Recommended Fix: 保留原始字幕文本换行结构；去重逻辑应只处理明显重复帧，而不是所有相同文本块。

Severity: MINOR
File: ui/app.py
Location: Web UI processing flow
Evidence: UI 已实现 URL 输入、本地上传、字幕展示、Markdown 展示、ZIP 下载等功能。
Reason: 满足基础 UI 验收，但长视频处理过程运行在 Streamlit 主线程，没有任务队列或取消机制，长 Whisper 转录时可能造成页面阻塞。
Recommended Fix: 增加 cookies 输入与持久化支持，增加 Mock 模式切换开关。

Final Verdict
存在 MAJOR 问题，当前实现完成了视频知识提取器 MVP 主框架，需要修复 MAJOR 项后重新验证。
```
