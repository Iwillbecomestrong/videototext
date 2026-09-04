# AGENT_CORE: 视频知识提取器 (video-knowledge-extractor)

## 1. 协作原则与真相源
- **项目定位**：视频知识提取工具与 AI Skill（输入视频链接/文件 -> 提取字幕 -> 领域术语纠正 -> 生成知识笔记与多版本字幕）。
- **单一真相源 (Single Source of Truth)**：
  - 需求与边界：`docs/specs/video-knowledge-extractor.md`
  - 实施路线与状态：`PLAN.md`（或 `docs/plans/`）
  - 核心决策与教训：`HISTORY.md`
  - 架构与目录地图：`README.md`
- **外部产物隔离**：所有 Web GPT 原始交互、推理草稿与临时 Review 报告统一存放在 `docs/work/`，不得污染正式文档。

## 2. 规范与门禁
- **Local README Gate**：修改或新建任何子目录前，必须确认该目录的职责与边界。
- **TDD 规则**：核心逻辑（字幕解析、术语替换、模板渲染、下载与抽取编排）先写失败测试（RED），再写最小实现（GREEN），再重构（REFACTOR）。
- **Git 规范**：遵循全局规范 `type(scope): 中文简述`（如 `spec(core)`、`test(cleaner)`、`feat(cli)`、`feat(ui)`、`chore(repo)`）。
