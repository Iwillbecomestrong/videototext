# Clarification Record: video-knowledge-extractor

## 1. User Goal
将视频（B站/YouTube等 URL，或本地音视频文件）自动转换为高价值技术学习资产：
提取字幕 -> 领域专业词汇纠正（FOC、STM32、ROS、AI 等）-> 输出原始字幕 (.srt)、校正版字幕 (_corrected.srt) 和 AI 知识笔记 (.md)，并封装为跨框架可调用的 AI Skill (`video-knowledge-extractor`) 与独立 Web UI。
代码托管于 GitHub: `https://github.com/Iwillbecomestrong/videototext/`。

## 2. Confirmed Behavior (MVP M1)
- **输入支持**：
  - URL 输入（B站、YouTube 等，利用 `yt-dlp` 提取已有字幕或下载音频）。
  - 本地文件上传（mp4, mkv, mp3, wav, m4a 等，利用 `ffmpeg` 提取音频并通过 Whisper/faster-whisper 转录）。
- **字幕处理管线**：
  - 字幕检测：视频自带官方/CC字幕时直接下载转换为 SRT 格式；无字幕时降级调用 Whisper 转录。
  - 术语校正：加载 `config/glossary.json`（支持 motor-control/embedded 等领域模式预设），利用高精度文本正则/词典替换常见 ASR 误识别词（如 "foo c" -> "FOC", "cooper mix" -> "CubeMX" 等），生成 `_corrected.srt`。
- **知识整理**：
  - 基于提示词模板 `templates/note_template.md`，通过兼容 OpenAI 协议的 LLM 接口，将校正字幕整理为结构化 Markdown 学习笔记（工具链、核心参数、核心原理、开发流程、代码要点）。
- **产物输出**：
  - 原始字幕：`[title].srt`
  - 校正版字幕：`[title]_corrected.srt`
  - AI 整理笔记：`[title]_notes.md`
  - 提取元数据/术语表：`[title]_glossary.json`
- **交付形态**：
  - 规范的 AI Skill 结构（含 `SKILL.md`，适配 Gemini / Claude / Codex 等）。
  - 模块化 Python 脚本 CLI (`scripts/`)。
  - 交互式 Web UI (Streamlit 应用 `ui/app.py`，支持链接输入/文件上传、领域选择、一键生成、预览与打包下载)。

## 3. Non-Goals (M1 MVP 暂不包含)
- 视频切片向量化与 Chroma/FAISS 本地 RAG 向量检索问答（规划于 M2 增强）。
- 自动提取视频画面截图并嵌入 Markdown（规划于 M2）。
- 复杂的多用户登录与权限系统。

## 4. Constraints
- 平台环境：Windows 11, Python 3.13.5, ffmpeg 8.1.1 已就绪。
- 并行与性能：遵循全局多核并行规则（空闲线程一半以内）。
- 依赖轻量化：LLM 请求支持 OpenAI-compatible API（兼容 DeepSeek、通义千问、OpenAI 等环境变量配置），支持无 API Key 时的离线 Mock/Dry-run 模式便于本地测试。
- 依赖容错：若未安装 faster-whisper/yt-dlp，提供明确的安装提示并允许测试模式降级。

## 5. Acceptance Criteria
- 单元测试与端到端测试覆盖：
  - SRT 解析与序列化测试。
  - 专业词汇库替换准确性测试（大小写敏感/不敏感匹配、边界匹配）。
  - LLM 笔记生成提示词与流式/同步调用契约测试。
  - 管线调度端到端测试（Mock 下载与 Mock 转写）。
- Skill 结构完整并符合 AI 工具箱规范。
- Streamlit Web UI 可正常启动并可预览和下载生成的文件。
- 远程仓库 `Iwillbecomestrong/videototext` 成功关联、审查并推送主分支代码。

## 6. Affected Modules
- `SKILL.md`
- `README.md`
- `scripts/extract_subtitle.py`
- `scripts/download_video.py`
- `scripts/whisper_transcribe.py`
- `scripts/subtitle_cleaner.py`
- `scripts/markdown_generator.py`
- `scripts/pipeline.py`
- `ui/app.py`
- `config/glossary.json`
- `templates/note_template.md`
- `tests/`
- `requirements.txt` / `pyproject.toml`

## 7. Open Questions
- 1. LLM 接口首选默认配置：默认通过标准环境变量 `OPENAI_API_KEY` 与 `OPENAI_BASE_URL`（可支持 DeepSeek、Qwen、OpenAI 等）接入，还是提供可直接在 UI 界面填入 Key 的选项？
- 2. 术语库分类：是否首发内置“电机控制与嵌入式 (motor-control/embedded)”和“通用计算机与AI (computer-ai)”两套领域字典，并支持用户自定义扩展？

## 8. SPEC Path
- `docs/specs/video-knowledge-extractor.md`
