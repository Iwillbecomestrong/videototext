---
name: video-knowledge-extractor
description: 输入视频链接或本地音视频文件，自动提取字幕、进行技术领域专业词纠正，并生成结构化工程学习笔记与标准字幕文件。
---

# Video Knowledge Extractor Skill

## 1. 适用场景
当用户需要：
- 从 Bilibili、YouTube 或其他网站视频链接提取字幕并整理成学习笔记；
- 处理本地音视频课程文件（mp4, mkv, wav, mp3 等），生成带时间戳的字幕与技术总结；
- 针对电机控制 (FOC/SVPWM)、STM32/嵌入式、ROS 或 AI 领域视频，纠正常见语音识别（ASR）错词（如 "foo c" ➜ "FOC", "cooper mix" ➜ "CubeMX", "无法加" ➜ "VOFA+" 等）；
- 输出高质量 Markdown 笔记（包含工具链、关键参数、原理推导、代码流程与避坑指南）。

---

## 2. 运行方式

### 命令行调用 (CLI)
可以直接在终端执行总控管线：
```powershell
python -m scripts.pipeline "<视频链接或本地文件路径>" [选项]
```

常用参数：
- `--domain`: 领域术语库，可选 `motor-control`（默认，适用于电机与嵌入式）或 `general-tech`。
- `--output`: 输出目录，默认为 `./output`。
- `--api-key`: OpenAI 兼容 API 密钥（可留空，系统自动使用环境变量 `OPENAI_API_KEY` 或切换为离线规则生成）。
- `--base-url`: OpenAI 兼容端点（如 `https://api.deepseek.com/v1`）。
- `--model`: 模型名（如 `deepseek-chat` 或 `gpt-4o`）。
- `--force-whisper`: 强制启用本地 Whisper 转写（即使视频自带原生字幕）。

示例：
```powershell
# B站链接提取
python -m scripts.pipeline "https://www.bilibili.com/video/BV123456" --domain motor-control

# 本地视频课程提取
python -m scripts.pipeline "FOC课程第一讲.mp4" --domain motor-control
```

---

### Python 代码调用
```python
from scripts.pipeline import KnowledgeExtractionPipeline

pipeline = KnowledgeExtractionPipeline(output_base_dir="./output", domain="motor-control")
result = pipeline.process(
    input_source="https://www.bilibili.com/video/BV123456",
    domain="motor-control"
)

print(result.title)
print(result.raw_srt_path)
print(result.corrected_srt_path)
print(result.notes_md_path)
print(result.terms_json_path)
```

---

### 启动交互式 Web UI
```powershell
streamlit run ui/app.py
```
启动后可在浏览器中使用直观的图形化工作台，支持 URL 提取、文件拖拽上传、领域选择、实时进度跟踪、产物对比预览与一键 ZIP 打包下载。

---

## 3. 产物交付规范
对于每一个处理的视频，系统将在输出目录下创建独立文件夹：
```text
output/
└── [视频标题]/
    ├── [视频标题]_raw.srt         # 原始提取字幕 (保持原始识别文字)
    ├── [视频标题]_corrected.srt   # 术语纠错版字幕 (时间戳严密对齐，术语纠正)
    ├── [视频标题]_notes.md       # AI 整理工程技术学习笔记
    └── [视频标题]_terms.json      # 术语命中与替换统计
```
