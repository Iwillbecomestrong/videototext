# Video Knowledge Extractor (视频知识提取器)

> ⚡ **专为工程与技术学习者打造的视频知识提取 Skill 与工具系统**  
> 支持 B站 / YouTube 等视频链接或本地音视频文件 ➜ 智能抓取/转录字幕 ➜ 领域专业术语纠错 (FOC/STM32/ROS/AI) ➜ 沉淀结构化工程学习笔记。

---

## 🌟 核心特性

- 🌐 **双输入模式**：
  - **URL 链接**：支持 B站、YouTube 等常见平台，通过 `yt-dlp` 智能探测官方字幕。
  - **本地文件**：支持 MP4、MKV、WAV、MP3 等多格式，无字幕自动使用 `Whisper` / `faster-whisper` 转录。
- 🎯 **领域专有名词纠错 (Glossary Engine)**：
  - 内置针对电机控制（FOC、CubeMX、VOFA+、Keil、Clarke/Park变换、SVPWM）与通用 AI/开发的技术词库。
  - 严格保持 SRT 序号与毫秒级时间轴不变，消除 ASR 常见谐音错词。
- 📚 **结构化工程笔记生成**：
  - 基于提示词模板，提炼核心概览、工具链依赖、配置参数、算法原理、代码流程与避坑指南。
  - 支持 OpenAI 兼容接口（DeepSeek、Qwen、OpenAI 等），亦支持无 API Key 离线规则降级生成。
- 🖥️ **现代化交互 Web UI**：
  - 内置 Streamlit 仪表盘，支持实时进度反馈、原始/校正字幕对比预览、笔记 Markdown 渲染、以及全部产物一键打包 ZIP 下载。
- 🧩 **标准 AI Agent Skill**：
  - 遵循 AI Agent Skill 规范，包含 `SKILL.md`，可无缝挂载至 Gemini、Claude、Codex 等 AI 智能体体系作为内置能力。

---

## 🏗️ 架构与数据流

```text
                 用户输入 (URL 或 本地音视频文件)
                               |
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
        【URL 输入】                           【文件输入】
      (yt-dlp 探测/抓取)                      (ffmpeg 提取音频)
            │                                     │
            ├───────────────┐                     │
            ▼               ▼                     │
     [存在官方字幕]    [无官方字幕]               │
            │               │                     │
      下载 SRT/VTT    下载音频 (.m4a/.mp3)        │
            │               └──────────┬──────────┘
            │                          ▼
            │               【Whisper / faster-whisper】
            │                 (本地 ASR 转录为 SRT)
            │                          │
            └───────────────┬──────────┘
                            ▼
                    【原始字幕生成】
                      (xxx.srt)
                            │
                            ▼
                 【专业术语纠正 Cleaner】
          (加载 config/glossary.json 领域词库)
                            │
                            ▼
                   【校正字幕生成】
                  (xxx_corrected.srt)
                            │
                            ▼
                 【AI 知识笔记生成 Generator】
            (基于 templates/note_template.md + LLM)
                            │
                            ▼
              ┌─────────────┴─────────────┐
              ▼                           ▼
       【知识笔记 Markdown】         【术语匹配表 JSON】
        (xxx_notes.md)             (xxx_terms.json)
```

---

## 🚀 快速启动

### 1. 安装依赖
确保已安装 Python 3.10+ 及 ffmpeg。
```bash
pip install -r requirements.txt
```

### 2. 启动 Web UI
```bash
streamlit run ui/app.py
```
浏览器打开 `http://localhost:8501` 即可体验图形化提取工作台。

### 3. 命令行调用 (CLI)
```bash
# 提取指定视频链接（使用电机控制领域词库）
python -m scripts.pipeline "https://www.bilibili.com/video/BV123456" --domain motor-control

# 处理本地录播视频文件
python -m scripts.pipeline "FOC实战课程.mp4" --domain motor-control
```

---

## 📁 产物目录规范

每次提取后，所有资产将按视频标题归档于 `./output/`：
```text
output/
└── STM32G431_FOC入门/
    ├── STM32G431_FOC入门_raw.srt         # 原始字幕
    ├── STM32G431_FOC入门_corrected.srt   # 术语纠错版字幕
    ├── STM32G431_FOC入门_notes.md       # AI 整理工程技术笔记
    └── STM32G431_FOC入门_terms.json      # 术语统计与替换明细
```

---

## ⚙️ 领域词库与模板扩展

- **扩展词库**：直接编辑 [config/glossary.json](config/glossary.json)，在对应分类下添加 `"识别误词": "标准术语"` 映射。
- **自定义笔记结构**：编辑 [templates/note_template.md](templates/note_template.md) 调整提炼小结的章节与版式。

---

## 🧪 自动化测试

项目严格遵循 TDD（测试驱动开发）原则编写：
```bash
python -m pytest -v
```

---

## 📄 开源协议
MIT License
