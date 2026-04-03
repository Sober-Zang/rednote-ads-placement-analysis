# Project Spec

状态：Phase 1 已锁定

## Product

### 目标用户

- 转转内部广告投放分析专员、内容策略人员、方法论沉淀负责人
- 需要对多个小红书优质图文样本做可回溯分析的内部研究用户

### 问题定义

- 输入通常是用户在自然语言中混排的多个小红书分享链接，夹杂标题文本、复制提示语甚至非小红书链接。
- 用户希望不仅得到逐篇分析，还要得到“为什么这些样本都能拿到好数据”的共性机制总结。
- 分析必须附带证据引用，并将输入、过程、输出统一保存到本地，便于复查与沉淀方法论。

### 核心用户流程

1. 用户在对话中提供一个或多个链接，可能夹杂标题、复制提示语与额外分析要求。
2. Skill 先提取链接并筛出 `http://xhslink.com/` 链接，记录非小红书链接但不纳入后续分析。
3. Skill 判断是否使用标准分析 Prompt。
4. Skill 调用小红书数据获取能力，围绕每个有效链接收集文本、图片、评论、互动数据和辅助元数据。
5. Skill 按 run 规则整理本地目录，并为每个链接建立可引用的证据锚点。
6. Skill 生成每篇图文的独立分析报告。
7. 如果有效链接数大于 1，Skill 再基于本次 run 的全部单篇报告生成综合分析报告。
8. Skill 输出最终播报，说明输出目录、生成文件及被排除的非小红书链接。

## Engineering

### 技术栈

- 前端：无。MVP 不做独立前端或 Web UI。
- 后端：Python 驱动的通用 Agent Skill 仓库形态。
- 数据存储：本地文件系统；结构化数据使用 JSON，报告使用 Markdown。
- 部署：本地执行优先，不做云部署设计。
- 鉴权：无独立鉴权系统；依赖宿主 Agent 与本地环境。
- 其他集成：
  - 小红书采集能力以 `MediaCrawler` 为研究型能力来源
  - Skill 结构与文风以 `video-copy-analyzer` 为基座
  - LLM 分析由宿主 Agent 负责，不在 MVP 内新增单独模型服务层

## Architecture

### 模块划分

- 输入解析层：从自然语言中提取链接、标题伴随文本与用户额外要求。
- 链接分类层：区分有效小红书链接与无效/非目标链接。
- Prompt 路由层：决定使用标准 Prompt 资产还是 run 专属 Prompt。
- 数据采集编排层：承接 `MediaCrawler` 相关小红书能力，围绕有效链接收集内容资产。
- 归档整理层：创建 run 目录、单链接目录和引用索引。
- 单篇分析层：基于单个链接的本地材料生成单篇 Markdown 报告。
- 综合分析层：基于本次 run 的全部单篇报告生成综合报告。
- 最终播报层：生成输出目录、报告链接与排除说明。

### 数据模型 / Schema

- `run_manifest.json`
  - `run_id`
  - `created_at`
  - `task_slug`
  - `source_prompt_mode` (`standard` / `run-specific`)
  - `valid_links`
  - `invalid_links`
  - `note_folders`
  - `outputs`
- `link_manifest.json`
  - `raw_text_fragment`
  - `raw_url`
  - `normalized_url`
  - `platform`
  - `is_valid_xhs`
  - `exclude_reason`
- `note_manifest.json`
  - `note_id`
  - `title`
  - `author_nickname`
  - `source_url`
  - `available_assets`
  - `primary_files`
  - `analysis_report_path`
- `reference_index.json`
  - `ref_id`
  - `ref_type` (`text` / `image` / `comment` / `data`)
  - `absolute_path`
  - `position`
  - `excerpt`

### API / 接口草案

- 输入接口
  - 输入形式：用户自然语言消息
  - 输入内容：多个可能混排的小红书链接，可附带额外分析要求
- 输出接口
  - 单篇报告：`<图文标题+作者名>_分析报告.md`
  - 综合报告：`<本次总结出的共有特点+时间戳>_综合分析报告.md`
  - 最终播报：输出目录、生成文件、快速打开链接、被剔除链接说明
- Prompt 选择接口
  - 条件 1：无额外要求，走标准 Prompt
  - 条件 2：用户目标与标准任务严格等价，走标准 Prompt
  - 条件 3：其余情况，写入 run 内专属 Prompt 并引用

## Constraints

- `Original_Prompt.md` 不可改动。
- 当前里程碑只做文档锁定，不写代码。
- `SKILL.md` 的未来结构必须强对齐 `video-copy-analyzer`，但本阶段不创建该文件。
- `MediaCrawler` 的小红书能力是总范围内的重要来源，但 MVP 闭环优先围绕“用户上传链接的明细抓取与分析”。
- 所有结论必须有明确引用来源；不得输出无证据支撑的武断判断。
- 所有产物必须落本地文件系统，并按 run 隔离。

## Milestones

### MVP

- 范围：
  - 多链接输入解析与小红书链接筛选
  - 明细抓取闭环的文档级规格锁定
  - 标准 Prompt / run Prompt 路由规则锁定
  - 单篇报告与综合报告的格式、命名、引用规则锁定
  - 上游复用边界、run 目录与本地落盘规则锁定
- 验收：
  - 文档足以让下一阶段实现者直接开始实现
  - 没有阻塞性歧义
  - 没有把非 MVP 的扩展能力混入当前闭环
- 风险：
  - `MediaCrawler` 的研究型许可与未来商业化目标之间存在潜在冲突
  - 上游项目实际结构可能与当前文档假设存在差异，需要实现前再做代码级核查

### V2

- 范围：
  - 将 `MediaCrawler` 其余小红书相关能力做可配置复用映射
  - 补足关键词搜索、指定帖子 ID、创作者主页、代理池、词云图等在本项目中的调用边界
  - 增强 run 内过程数据索引与错误处理文档
- 验收：
  - 扩展能力接入后仍不破坏 MVP 主闭环
  - 各能力的输入输出和落盘位置可预测
- 风险：
  - 上游依赖复杂度上升
  - 运行环境与宿主适配成本上升

### V3

- 范围：
  - 自动化评测流水线
  - 更强的素材对比、方法论版本管理和团队复盘能力
  - 若合规允许，再评估更广泛的内部试运行形态
- 验收：
  - Skill 迭代有稳定评估机制
  - 结果沉淀可支持团队规模化复用
- 风险：
  - 评测设计可能偏离真实业务价值
  - 合规与运维成本会进一步增加

## Backlog

- 独立 Web UI
- 云端部署
- 外部分发版本
- 非小红书平台扩展
- 自动化 benchmark 实现代码
