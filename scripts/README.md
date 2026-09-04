# Scripts 目录职责
存放视频下载、字幕抓取与转换、ASR 转录、术语纠正、AI 笔记生成以及总控管线核心业务模块。
- `subtitle_cleaner.py`: 专业术语纠正与 SRT 块重写
- `extract_subtitle.py`: 官方/在线字幕探测与 VTT->SRT 转换
- `download_video.py`: 音频流下载与格式转换
- `whisper_transcribe.py`: 本地 ASR 转录封装
- `markdown_generator.py`: LLM 知识笔记组织与生成
- `pipeline.py`: 端到端提取管线总控与 CLI 入口
