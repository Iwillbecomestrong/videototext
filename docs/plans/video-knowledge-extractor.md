# PLAN: 视频知识提取器 (video-knowledge-extractor) 实现计划

本计划由 Web GPT Plan (`docs/work/plan-raw.md`) 与正式 SPEC 严格对齐整合而成，拆分为 6 个垂直 TDD 任务。

---

## 任务拆分与执行路线 (Vertical TDD Tasks)

### Task 1: 项目基础骨架与领域配置 (Foundation & Config)
- **目标**：建立项目依赖清单、词库与笔记模板、环境自检测试。
- **文件**：
  - `requirements.txt`
  - `pyproject.toml`
  - `config/glossary.json` (内置 motor-control 与 general-tech 词库)
  - `templates/note_template.md` (工程技术学习笔记模板)
  - `tests/test_environment.py` (词库加载、模板校验)
- **TDD 验收**：测试词库结构有效性与模板完整性通过。

### Task 2: 专业术语纠正引擎 (Subtitle Cleaner)
- **目标**：高精度 SRT 词库替换，保护时间戳与序号，支持短语优先与大小写不敏感匹配，输出纠错统计。
- **文件**：
  - `scripts/subtitle_cleaner.py`
  - `tests/test_subtitle_cleaner.py`
- **TDD 验收**：
  - RED: 编写包含 FOC/CubeMX/VOFA+/时间戳混淆的多行测试用例。
  - GREEN: 实现词库规范化、短语/单词正则匹配与 SRT 块重构。
  - REFACTOR: 优化正则执行效率并保证统计数据准确。

### Task 3: 在线字幕抓取与 VTT/SRT 解析 (Subtitle Extraction)
- **目标**：基于 `yt-dlp` 探测并提取视频原生字幕，支持 VTT -> SRT 格式归一化、毫秒小数点转换、缺失序号修复。
- **文件**：
  - `scripts/extract_subtitle.py`
  - `tests/test_extract_subtitle.py`
- **TDD 验收**：
  - RED: 针对 VTT 文本、无序号 SRT、不同编码字幕编写解析转换断言。
  - GREEN: 实现 `fetch_online_subtitles` 与 `vtt_to_srt` 转换器。
  - REFACTOR: 增强防崩溃处理与空字幕降级返回。

### Task 4: 音频下载与 Whisper ASR 转录 (Audio Download & Transcribe)
- **目标**：当无原生字幕时，下载音频流并通过 faster-whisper/whisper 进行本地 ASR 转录，生成规范 SRT。
- **文件**：
  - `scripts/download_video.py`
  - `scripts/whisper_transcribe.py`
  - `tests/test_whisper_transcribe.py`
- **TDD 验收**：
  - RED: 针对依赖缺失、Mock ASR 返回编写测试用例。
  - GREEN: 实现音频提取与转录流，包含清晰安装引导。
  - REFACTOR: 保证在未安装 heavy ASR 权重时的测试桩稳定运行。

### Task 5: AI 结构化知识笔记生成器 (Markdown Generator)
- **目标**：将校正字幕结合模板组织 prompt，调用兼容 OpenAI 协议的 LLM 生成 Markdown 笔记；支持离线规则降级。
- **文件**：
  - `scripts/markdown_generator.py`
  - `tests/test_markdown_generator.py`
- **TDD 验收**：
  - RED: 验证提示词构造、Mock LLM 响应解析、无 Key 时的离线 Mock 摘要生成。
  - GREEN: 封装 `MarkdownGenerator` 类并支持 API Key / Base URL / Model 参数与环境变量。
  - REFACTOR: 格式清理与容错解析。

### Task 6: 总控管线、Web UI 与 Skill 定义 (Pipeline, UI & Skill)
- **目标**：打通统一 CLI/Pipeline、构建现代交互式 Streamlit Web UI、编写标准 `SKILL.md` 与根 `README.md`。
- **文件**：
  - `scripts/pipeline.py`
  - `tests/test_pipeline.py`
  - `ui/app.py`
  - `SKILL.md`
  - `README.md`
- **TDD 验收**：
  - 端到端测试跑通：模拟输入 URL/文件 -> 产出 4 份目标文件。
  - Streamlit 应用无语法错误且各交互组件正常加载。
  - Git Commit、Review 审查并通过 `git push origin main` 交付。
