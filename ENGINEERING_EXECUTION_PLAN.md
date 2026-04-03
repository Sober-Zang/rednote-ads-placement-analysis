# ENGINEERING_EXECUTION_PLAN

状态：Phase 2 MVP 工程执行规划已锁定  
用途：为本项目的 MVP 工程落地提供可直接执行的工作包级计划，明确文档优先级、执行顺序、依赖关系、DoD 与同步动作。

## 1. 项目执行目标与范围

### 1.1 本阶段目标

进入 Phase 2，仅围绕 MVP 建造一条可执行的工程落地闭环，使后续实现能够严格依据仓库文档推进，而不是依赖对话记忆。

本阶段的目标不是直接实现所有功能，而是：

- 把当前 Phase 1 已冻结的需求与规格，转化为工程执行顺序
- 把 MVP 拆解成可独立推进的工作包
- 明确每个工作包需要调用哪些文档，以及各文档在该步中的作用
- 明确每个工作包的输出、验收、依赖与同步要求

### 1.2 本阶段范围

仅锁定 MVP 的工程落地顺序，不展开 V2/V3 的实现细节。

MVP 主闭环为：

1. 用户输入多个混合文本中的小红书链接
2. 解析并筛出有效小红书链接
3. 围绕每个有效链接下载与整理小红书数据
4. 为每个有效样本生成单篇分析报告
5. 对多样本生成综合分析报告
6. 将输入、Prompt、原始数据、分析报告与最终播报统一落到 run 目录

### 1.3 不在本阶段展开的内容

- V2 中 `MediaCrawler` 扩展能力的完整接入细节
- V3 中自动化评测流水线、方法论版本管理和更广泛内部试运行
- 云端部署、Web UI、外部分发

## 2. 文档优先级与调用顺序

### 2.1 文档工程影响优先级

#### P0 不可变源与强约束

- `RAPA_Support_Documents/Original_Prompt.md`
- `RAPA_Support_Documents/ENGINEERING_RULES.md`
- `Project.md`

#### P1 直接定义 MVP 执行目标与接口

- `docs/project-spec.md`
- `docs/skill-draft.md`
- `docs/run-blueprint.md`
- `docs/eval-plan.md`

#### P2 提供边界、上下文与写法基线

- `docs/project-brief.md`
- `docs/skill-draft-guide.md`
- `docs/architecture.md`
- `skills/skill-creator/SKILL.md`

#### P3 执行同步与过程记录

- `docs/status.md`
- `docs/changelog.md`
- `docs/feature-notes/_template.md`

#### P4 辅助自动化与仓库守卫

- `Makefile`
- `scripts/build_with_skill.sh`
- `scripts/skill_state.sh`
- `scripts/validate_skill_creator_env.py`
- `.skill-control/skill-creator.state`

### 2.2 入场顺序

每次进入工程执行会话，按以下顺序读取：

1. `Project.md`
2. `docs/status.md`
3. `docs/project-spec.md`
4. `docs/skill-draft.md`
5. `docs/run-blueprint.md`
6. `docs/eval-plan.md`
7. 若出现冲突或边界不清，再回看 `RAPA_Support_Documents/ENGINEERING_RULES.md`

### 2.3 冲突裁决顺序

当多个文档出现冲突时，按以下顺序裁决：

1. `RAPA_Support_Documents/Original_Prompt.md`
2. `RAPA_Support_Documents/ENGINEERING_RULES.md`
3. `Project.md`
4. `docs/project-spec.md`
5. `docs/skill-draft.md`
6. `docs/run-blueprint.md` / `docs/eval-plan.md`

补充说明：

- `docs/skill-draft-guide.md` 只作为 `skill-draft.md` 的撰写约束参考，不作为工程规格真源
- `skills/skill-creator/SKILL.md` 只作为外接 skill 的方法论来源，不参与业务规格裁决

### 2.4 各关键文档在工程执行中的作用

| 文档 | 工程作用 | 重点关注细节 |
|------|----------|--------------|
| `Original_Prompt.md` | 产品北极星与最终输出要求 | 完整提示词、报告格式、run 落盘、最终播报 |
| `ENGINEERING_RULES.md` | 工程红线与 DoD | `Research -> Plan -> Implement -> Test & Sync`、禁止范围蔓延、文档同步 |
| `Project.md` | 入口索引与当前主线 | 当前阶段、不可变约束、更新循环 |
| `docs/project-spec.md` | MVP 执行规格真源 | 核心流程、模块划分、数据模型、接口草案、MVP 范围 |
| `docs/skill-draft.md` | 未来真实 `SKILL.md` 的内容蓝本 | 5 阶段 workflow、标准 Prompt、最终播报、安装验证结构 |
| `docs/run-blueprint.md` | 落盘与命名真源 | run 命名、样本目录、manifest、引用锚点、播报模板 |
| `docs/eval-plan.md` | 工程验收真源 | 主样本、边界场景、通过标准 |
| `docs/project-brief.md` | 高层目标与 MVP 边界 | 目标用户、核心问题、必须功能与可砍功能 |
| `docs/architecture.md` | 当前结构总览与文档分工 | 层级结构、后续模块登记要求 |
| `docs/status.md` | 当前停靠点与下一步 | 当前阶段、阻塞项、下个会话读取链路 |

## 3. MVP 工作包拆解

所有工作包都必须遵守：

- 先 Research / Plan，后 Implement
- 单个工作包不得偷跑到后续工作包内容
- 完成后必须执行 Test & Sync

### WP0 代码级对标研究

#### 目标

核验 `MediaCrawler` 与 `video-copy-analyzer` 的实际代码结构、目录布局、依赖要求与许可现实，确认是否支持当前 Phase 1 文档中的假设。

#### 输入文档

- `RAPA_Support_Documents/Original_Prompt.md`
- `docs/project-spec.md`
- `docs/skill-draft.md`
- `RAPA_Support_Documents/ENGINEERING_RULES.md`

#### 重点关注

- `MediaCrawler` 中小红书相关能力的真实入口、最小可复用面和运行依赖
- `video-copy-analyzer` 的真实 skill 目录与 `SKILL.md` 结构
- 文档假设与真实代码结构是否一致
- 许可、依赖、目录结构与复用边界是否存在阻塞项

#### 输出

- 研究结论
- 风险清单
- 最终接入边界
- 若有偏差，形成文档级修正建议

#### 依赖

- 无前置工作包，是 MVP 执行的起点

#### 验收

- 已确认两个上游仓库的现实结构与当前文档的差异
- 已明确最小复用方案
- 未进入任何实现

### WP1 skill 仓库骨架与入口定稿

#### 目标

将未来真实 skill 目录、`SKILL.md`、`assets/`、`references/`、`scripts/` 的最小结构定稿。

#### 输入文档

- `docs/skill-draft.md`
- `docs/skill-draft-guide.md`
- `RAPA_Support_Documents/ENGINEERING_RULES.md`
- `docs/project-spec.md`

#### 重点关注

- `video-copy-analyzer` 的结构强对齐
- 不破坏既定术语和目录主线
- 标准 Prompt 应进入未来 `assets/`
- run 专属 Prompt 不进入全局 `assets/`
- 只定稿最小可执行骨架，不提前扩展 V2/V3

#### 输出

- 真实实现要落的目录与文件清单
- 未来 skill 根目录结构定义
- 各目录职责说明

#### 依赖

- 依赖 `WP0` 的代码级对标研究结论

#### 验收

- 结构定稿不再依赖实现者临场决定
- 全局资产与 run 局部资产边界清晰

### WP2 输入解析与 Prompt 路由闭环

#### 目标

确定“自然语言提取链接 -> 判定小红书链接 -> 标准 / 专属 Prompt 分流”的完整实现闭环。

#### 输入文档

- `docs/project-spec.md`
- `docs/skill-draft.md`
- `docs/run-blueprint.md`
- `docs/eval-plan.md`

#### 重点关注

- `http://xhslink.com/` 链接判定规则
- 混杂标题文本、复制提示语和任务说明的区分
- 非小红书链接排除与最终点名说明
- 无额外要求或严格等价任务时使用标准 Prompt
- 非严格等价任务必须生成 run 专属 Prompt，且只落当前 run

#### 输出

- 输入处理逻辑
- 链接分类规则
- Prompt 文件落盘方案
- `link_manifest.json` 的字段定义细化

#### 依赖

- 依赖 `WP1` 的 skill 目录结构定稿

#### 验收

- 主检验样本中的 5 个小红书链接 + 1 个 GitHub 链接可被正确分类
- 标准 Prompt / run 专属 Prompt 分流逻辑明确

### WP3 小红书数据采集与样本归档闭环

#### 目标

确定“每个有效链接一个目录”的数据下载、整理、manifest 与引用索引闭环。

#### 输入文档

- `RAPA_Support_Documents/Original_Prompt.md`
- `docs/project-spec.md`
- `docs/run-blueprint.md`
- `docs/eval-plan.md`

#### 重点关注

- 文本、图片、评论、互动数据、辅助元数据和词云图等能力边界
- 单样本目录命名规则与原始标题 / 作者昵称保留
- `run_manifest.json`、`note_manifest.json`、`reference_index.json` 的落盘位置
- 数据整理后必须可供分析阶段直接消费

#### 输出

- 样本目录结构定义
- manifest 产物清单
- 引用锚点规范
- 原始数据向分析层的传递要求

#### 依赖

- 依赖 `WP0` 的上游能力核验
- 依赖 `WP2` 的输入解析结果结构

#### 验收

- 每个有效链接的样本目录结构明确
- 数据不会只停留在抓取层，已经为分析准备好
- 引用来源可追溯

### WP4 单篇分析与综合分析闭环

#### 目标

把标准 Prompt 对应到单篇报告和综合报告的真实生成链路。

#### 输入文档

- `docs/skill-draft.md`
- `RAPA_Support_Documents/Original_Prompt.md`
- `docs/eval-plan.md`
- `docs/run-blueprint.md`

#### 重点关注

- 单篇报告先于综合报告
- 综合报告只基于本次 run 的全部单篇报告
- 报告格式、引用标签、最终播报严格对齐 `Original_Prompt.md`
- 数据不足时可指出边界，但不能臆测

#### 输出

- 分析执行链路
- 单篇与综合报告生成规则
- 最终播报要求

#### 依赖

- 依赖 `WP2` 的 Prompt 路由规则
- 依赖 `WP3` 的样本归档与引用准备

#### 验收

- 单篇与综合报告的生成条件、输入和输出清晰
- 引用要求、报告结构和播报模板与北极星需求一致

### WP5 验收、评估与文档同步闭环

#### 目标

将主样本 eval、补充边界场景、DoD 和文档同步节奏绑定为工程完成闭环。

#### 输入文档

- `docs/eval-plan.md`
- `RAPA_Support_Documents/ENGINEERING_RULES.md`
- `Project.md`
- `docs/run-blueprint.md`
- `docs/feature-notes/_template.md`

#### 重点关注

- 主检验样本：5 个小红书链接 + 1 个 GitHub 链接
- 补充边界场景：0 有效链接、run 专属 Prompt
- DoD 必须包含：范围一致性、运行可验证、上下文已刷新、复盘已沉淀、集成无回归
- 完成后同步：
  - `docs/status.md`
  - `docs/changelog.md`
  - `docs/architecture.md`
  - 对应 `docs/feature-notes/`

#### 输出

- 验收清单
- 执行后文档同步动作
- 阻塞条件与失败回退条件

#### 依赖

- 依赖 `WP2/WP3/WP4` 的完整闭环定义

#### 验收

- 工程完成标准与文档同步动作绑定
- 实现者知道“什么时候算完成”和“完成后必须更新哪些文档”

## 4. 工作包之间的依赖关系

### 4.1 执行主链路

`WP0 -> WP1 -> WP2 -> WP3 -> WP4 -> WP5`

### 4.2 依赖说明

- `WP0` 是全部后续工作包的现实校验基础
- `WP1` 决定真实 skill 目录如何落地，是 `WP2` 的结构前置
- `WP2` 决定输入和 Prompt 路由，是 `WP3` 和 `WP4` 的逻辑入口
- `WP3` 负责把原始数据整理成分析可用材料，是 `WP4` 的数据前置
- `WP4` 负责形成最终业务输出，是 `WP5` 的验收对象
- `WP5` 负责把工程完成标准、主样本评估和文档同步闭环落地

### 4.3 并行边界

- 在 `WP0` 完成前，不允许并行推进真实接入方案
- `WP2` 与 `WP3` 不建议完全并行；因为 Prompt 路由、输入分类和样本结构需要先统一口径
- `WP5` 只能在 `WP4` 形成完整输出链路后定稿

## 5. DoD / 验收 / 文档同步规则

### 5.1 MVP 级完成定义

MVP 工程落地完成，至少满足：

1. 输入解析、Prompt 路由、样本归档、单篇分析、综合分析、最终播报形成一条闭环
2. 主检验样本可用于完整验证链路
3. 所有产物按 run 规则落本地
4. 关键结论均带引用来源
5. 相关上下文文档完成同步

### 5.2 每个工作包的通用 DoD

- 已完成对应 Research / Plan / Implement / Test & Sync
- 未偏离当前工作包范围
- 输出已落到仓库或 run 中的约定位置
- 与上游文档约束无冲突
- 已更新必要文档

### 5.3 文档同步规则

每完成一个工作包后，至少执行：

- `docs/status.md`
  - 更新当前停靠点、已完成工作包、下一步
- `docs/changelog.md`
  - 记录工作包级变更摘要

当工作包改变结构、目录、模块边界或术语时，额外更新：

- `docs/architecture.md`
- 对应 `docs/feature-notes/<feature>.md`

当发现新的防呆规则时：

- 将一句可执行规则回写到 `Project.md`

### 5.4 禁止事项

- 不得修改 `RAPA_Support_Documents/Original_Prompt.md`
- 不得未经过 Plan 确认直接进入 Implement
- 不得把 V2/V3 内容提前夹带进 MVP
- 不得把 run 专属 Prompt 写回全局 `assets/`
- 不得让数据只停留在下载层而不进入分析闭环

## 6. 风险、阻塞项与后续路线

### 6.1 当前已知风险

- `MediaCrawler` 的研究型许可与未来商业化目标可能存在冲突
- 当前文档对上游项目结构的假设仍需 `WP0` 代码级核验
- run 目录、manifest 和引用索引的真实字段在实现时可能需要微调，但不能破坏既定主线

### 6.2 阻塞条件

以下任一情况出现时，应暂停继续实现并先修正文档或结论：

- 上游实际结构与当前规格存在关键不一致
- 无法满足主样本 eval 的完整下载与合理落档要求
- 无法保证综合报告只基于本次 run
- 无法保持 `SKILL.md` 对 `video-copy-analyzer` 的结构强对齐

### 6.3 MVP 之后的路线

- V2：扩展 `MediaCrawler` 小红书能力映射，补齐关键词搜索、创作者主页、代理池、词云图等的真实接入边界
- V3：建立自动化评估流水线、方法论版本管理和更广泛内部试运行机制

### 6.4 下一步建议

后续实际工程执行应先从 `WP0 代码级对标研究` 开始，不应跳过这一层直接搭建 skill 代码或 run 逻辑。
