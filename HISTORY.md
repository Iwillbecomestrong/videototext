# HISTORY: 视频知识提取器迭代演进记录

## [2026-09-04] MVP 架构建立与 Web GPT 审查收敛 (v0.1.0)

### 1. 核心决策与里程碑
- **治理与真相源**：在 `i:\桌面\视频字幕` 初始化 Git 仓库并连接远程 GitHub `Iwillbecomestrong/videototext`，建立以 `AGENT_CORE.md`、`docs/specs/video-knowledge-extractor.md` 和 `PLAN.md` 为核心的治理体系。
- **管线架构**：
  - 双输入：URL 智能提取（优先原生字幕）+ 本地文件处理。
  - 核心引擎：
    - `subtitle_cleaner.py`：基于 `config/glossary.json`，在毫秒级时间轴和 SRT 块结构严密保护下执行大小写不敏感与短语优先的领域专有名词纠正。
    - `extract_subtitle.py`：集成 B站 原生 Web API 探测器与 yt-dlp 双轨方案，支持 JSON/VTT/SRT 格式转换与 Cookies 鉴权。
    - `whisper_transcribe.py`：优先调用 faster-whisper，无缝兼容 openai-whisper，提供降级引导。
    - `markdown_generator.py`：支持 OpenAI 兼容 API 调用、高保真结构化 Mock 模式（免 API Key 体验）以及离线规则降级。
    - `pipeline.py`：顶层总控引擎，对外输出 4 份标准化产物：`[title]_raw.srt`、`[title]_corrected.srt`、`[title]_notes.md`、`[title]_terms.json`。
  - 前端与交互：
    - `ui/app.py`：现代化 Streamlit 工作台，支持在线 URL 输入、文件上传、实时进度反馈、原始/校正字幕对比渲染、Markdown 在线渲染及一键打包 ZIP 下载。
    - `SKILL.md`：规范封装为标准 AI Agent Skill，支持多框架一键调度。

### 2. Web GPT Review 审查反馈与迭代修复
- **第一轮审查 (`eb9175d`)**：
  - 识别出 3 项 MAJOR 问题：
    1. 缺少明确的 Mock LLM 测试模式；
    2. B站字幕格式较多，通用探测不够稳定；
    3. Whisper 降级链路需要完善单元测试与断言。
  - 修复动作：
    - 增加 `mock=True` 模式，输出高保真结构化工程笔记；
    - 增加 Bilibili JSON 转换器与 cookies 参数支持；
    - 增加 `vtt_to_srt` 多行换行保护与 Whisper 回退测试。
- **第二轮审查与收敛 (`d69f340` -> `c3e3405`)**：
  - 增加 B站 原生 API 直连探测（通过 `x/web-interface/view` 直接提取字幕 JSON 并解析为 SRT，实现秒级解析并降低对 yt-dlp 解析器的单一依赖）；
  - 增加端到端三种典型流程集成测试（有字幕、Whisper 转录、LLM 失败优雅降级），全部 23 项测试顺利通过。
