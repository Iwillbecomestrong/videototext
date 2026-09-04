"""Streamlit Web UI for Video Knowledge Extractor."""

import io
import os
import shutil
import zipfile
from pathlib import Path
import streamlit as st

from scripts.pipeline import KnowledgeExtractionPipeline, PipelineResult


st.set_page_config(
    page_title="Video Knowledge AI - 视频知识提取器",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS styling for a modern, high-tech interface
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #3B82F6, #10B981);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #64748B;
        font-size: 1.05rem;
        margin-bottom: 1.8rem;
    }
    .metric-card {
        background-color: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        border-radius: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ 系统配置")

    domain_choice = st.selectbox(
        "🎯 领域专业词库",
        options=["motor-control", "general-tech"],
        format_func=lambda x: "电机控制与嵌入式 (FOC/STM32/ROS)" if x == "motor-control" else "通用技术与AI开发",
    )

    st.markdown("---")
    st.subheader("🤖 LLM 智能整理配置")
    use_mock_mode = st.checkbox(
        "💡 启用 Mock 演示模式 (免 API Key 体验)",
        value=False,
        help="开启后自动生成高质量结构化工程笔记样本，适合快速测试或无 API Key 场景",
    )

    env_key = os.environ.get("OPENAI_API_KEY", "")
    api_key_input = st.text_input(
        "API Key",
        value=env_key,
        type="password",
        placeholder="sk-...",
        help="OpenAI 兼容 API 密钥（DeepSeek / Qwen / OpenAI）",
    )

    env_base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    base_url_input = st.text_input(
        "Base URL",
        value=env_base,
        placeholder="https://api.deepseek.com/v1",
        help="API 基础端点",
    )

    env_model = os.environ.get("OPENAI_MODEL", "gpt-4o")
    model_input = st.text_input(
        "Model Name",
        value=env_model,
        placeholder="deepseek-chat",
        help="调用的模型标识",
    )

    st.markdown("---")
    st.subheader("🍪 B站 / 平台 Cookie 设置")
    cookie_input = st.text_input(
        "Cookie / SESSDATA (可选)",
        value="",
        placeholder="SESSDATA=xxxxxx; 或 cookies.txt 路径",
        help="部分 B站 视频或大会员字幕需登录权限，填入 Cookie 可直接下载官方字幕",
    )

    force_whisper = st.checkbox(
        "强制启用 Whisper 本地转写",
        value=False,
        help="即使视频自带官方字幕，也强制使用本地 Whisper ASR 转录",
    )


# Header Area
st.markdown('<div class="main-title">⚡ Video Knowledge Extractor</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">输入视频链接或上传音视频 ➜ 自动提取字幕 ➜ 领域专有名词纠错 ➜ 输出规范字幕与结构化工程学习笔记</div>',
    unsafe_allow_html=True,
)

# Input Section
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("### 🌐 模式 A：视频 URL")
    url_input = st.text_input(
        "视频链接 (支持 B站、YouTube、Vimeo 等)",
        placeholder="https://www.bilibili.com/video/BV...",
        key="video_url",
    )
    st.caption("示例：STM32、FOC 驱动开发、电机控制或前沿 AI 论文精读视频")

with col2:
    st.markdown("### 📁 模式 B：本地音视频上传")
    uploaded_file = st.file_uploader(
        "选择本地视频或音频文件",
        type=["mp4", "mkv", "avi", "mov", "mp3", "wav", "m4a", "flac"],
        key="file_upload",
    )
    st.caption("支持常见格式，视频将自动通过 ffmpeg 抽离音频")

start_btn = st.button("🚀 开始知识提取", type="primary", use_container_width=True)

# Processing Logic
if start_btn:
    input_source = None
    temp_file_path = None

    if url_input and url_input.strip():
        input_source = url_input.strip()
    elif uploaded_file is not None:
        temp_dir = Path("./temp_uploads")
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_file_path = temp_dir / uploaded_file.name
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        input_source = str(temp_file_path)
    else:
        st.warning("⚠️ 请在上方输入视频链接或上传本地音视频文件！")

    if input_source:
        progress_bar = st.progress(0.0)
        status_text = st.empty()

        def update_progress(msg: str, progress: float):
            progress_bar.progress(progress)
            status_text.info(f"⏳ {msg}")

        try:
            pipeline = KnowledgeExtractionPipeline(
                output_base_dir="./output", domain=domain_choice
            )
            result = pipeline.process(
                input_source=input_source,
                domain=domain_choice,
                api_key=api_key_input if api_key_input.strip() else None,
                base_url=base_url_input if base_url_input.strip() else None,
                model=model_input if model_input.strip() else None,
                force_whisper=force_whisper,
                cookies=cookie_input.strip() if cookie_input.strip() else None,
                mock=use_mock_mode,
                progress_callback=update_progress,
            )

            progress_bar.progress(1.0)
            status_text.success("🎉 提取与整理完成！")
            st.session_state["last_result"] = result

        except Exception as e:
            progress_bar.empty()
            status_text.error(f"❌ 处理发生错误: {str(e)}")
            st.exception(e)

# Results Display Area
if "last_result" in st.session_state:
    res: PipelineResult = st.session_state["last_result"]
    st.markdown("---")
    st.subheader(f"📖 提取成果: {res.title}")

    # Metrics Summary
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("领域分类", domain_choice)
    with m2:
        st.metric("术语校正命中", f"{res.terms_count} 处")
    with m3:
        st.metric("产物存储目录", Path(res.output_dir).name)
    with m4:
        # Create ZIP download
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for p in [res.raw_srt_path, res.corrected_srt_path, res.notes_md_path, res.terms_json_path]:
                if Path(p).exists():
                    zip_file.write(p, arcname=Path(p).name)
        zip_buffer.seek(0)
        st.download_button(
            label="📦 一键打包下载全部产物 (ZIP)",
            data=zip_buffer,
            file_name=f"{Path(res.output_dir).name}_knowledge.zip",
            mime="application/zip",
            use_container_width=True,
        )

    # Content Tabs
    tab_notes, tab_corrected, tab_raw, tab_terms = st.tabs(
        ["📚 AI 整理学习笔记", "✨ 校正版字幕 (.srt)", "📝 原始字幕 (.srt)", "🔍 术语命中表 (.json)"]
    )

    with tab_notes:
        notes_content = Path(res.notes_md_path).read_text(encoding="utf-8")
        st.download_button(
            "📥 下载学习笔记 (.md)",
            data=notes_content,
            file_name=Path(res.notes_md_path).name,
            mime="text/markdown",
        )
        st.markdown(notes_content)

    with tab_corrected:
        corr_content = Path(res.corrected_srt_path).read_text(encoding="utf-8")
        st.download_button(
            "📥 下载校正版字幕 (.srt)",
            data=corr_content,
            file_name=Path(res.corrected_srt_path).name,
            mime="text/plain",
        )
        st.text_area("校正版字幕内容", corr_content, height=400)

    with tab_raw:
        raw_content = Path(res.raw_srt_path).read_text(encoding="utf-8")
        st.download_button(
            "📥 下载原始字幕 (.srt)",
            data=raw_content,
            file_name=Path(res.raw_srt_path).name,
            mime="text/plain",
        )
        st.text_area("原始字幕内容", raw_content, height=400)

    with tab_terms:
        terms_content = Path(res.terms_json_path).read_text(encoding="utf-8")
        st.download_button(
            "📥 下载术语数据 (.json)",
            data=terms_content,
            file_name=Path(res.terms_json_path).name,
            mime="application/json",
        )
        st.json(terms_content)
