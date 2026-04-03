
**关联：[[Skill.md 口径经验]] · [[Agent Skill 部署]]**


**0-1 Vibe Coding（Antigravity）项目启动提示词包（PSB）**

  

**1) PLAN：15 分钟规划提示词**

  

**P0：目标对齐（先定"我要做什么"）**

  

你先不要写代码。请你问我 5 个澄清问题，逼我明确：

  

1. 我这个项目的真实目标（学习/验证想法/做MVP/上线给用户）

  

2. 目标用户是谁、核心问题是什么

  

3. MVP 的"必须功能"与"可砍功能"

  

4. 成功标准（可量化/可验收）

  

5. 约束（时间/成本/技术栈/安全/合规/不做什么）\

然后把我的回答整理成一页《Project Brief》（Markdown）。

  

**P1：里程碑拆分（MVP→V2→V3）**

  

基于 Project Brief，把项目拆成：MVP / V2 / V3 三个里程碑。\

每个里程碑写：范围（in/out）、验收标准、关键风险。\

强制把"以后再做"的内容放到 Backlog，不要混进 MVP。

  

**P2：Spec Doc 生成（产品 + 工程合一）**

  

请输出一个《Project Spec Doc》（轻量 PRD + 轻量 EDD 合体），包含：

  

- Product：目标用户、问题、核心用户流程（逐步步骤，不要一句话带过）

  

- Engineering：明确技术栈（前端/后端/DB/部署/鉴权/支付等按需），不允许你替我"随便选"

  

- Architecture：模块划分、数据模型/Schema、API/接口草案（若需要）

  

- Constraints：安全/合规/禁区（明确"禁止做什么"）

  

- Milestones：对应 MVP/V2/V3 的交付物\

要求：可直接作为 AI 编码的源文档。

  

**2) SETUP：Antigravity 项目落地提示词（7 步）**

  

**S1：Repo & Branch 纪律**

  

初始化 Git 仓库并给出推荐的分支策略：main + feature branches。\

规则：每个大功能一个分支；禁止直接 push main；所有合并走 PR/merge。\

输出：具体命令 + 分支命名规范。

  

**S2：环境变量（不要卡在 Key 上）**

  

根据 Project Spec 生成 .env.example，列出所有可能需要的变量名和说明。\

同时生成 .gitignore 规则，确保 secrets 不入库。

  

**S3：PROJECT.md（项目记忆，不要臃肿）**

  

生成一个 PROJECT.md 作为 AI 永久在线索引，要求：

  

- 只放"必须知道"的信息：目标、架构概览、目录结构、关键约束、工作流规则、常用命令

  

- 严禁堆细节；细节放到外链文档

  

- 在文件末尾写"指向其他文档的链接清单"（Spec/Architecture/Status 等）

  

**S4：自动化文档（把上下文从对话里搬到 repo）**

  

在 docs/ 下创建四个文件并给模板：

  

1. docs/architecture.md（系统结构与模块交互）

  

2. docs/changelog.md（变更记录）

  

3. docs/status.md（里程碑进度 + 上次停在哪）

  

4. docs/feature-notes/\<feature\>.md（关键功能规则与边界）\

要求：每完成一个功能，你要自动更新这些文档对应部分。

  

**S5：插件/技能（可选）**

  

如果项目需要前端 UI/工程化，请推荐 1-3

个插件/技能方向，并说明各自解决什么问题。\

不要堆列表，只保留"最有价值"的。

  

**S6：MCP（可选，但对自动化很关键）**

  

基于技术栈，建议需要接入哪些 MCP（数据库/测试/部署/分析）。\

每个 MCP 给：使用场景、能省掉哪些人工步骤、接入优先级（P0/P1/P2）。

  

**S7：Slash commands & Subagents（并行与复盘）**

  

设计 3 个最小可用的自动化命令/子代理：

  

1. update-docs：更新 docs + status

  

2. create-issues：把里程碑拆成 GitHub issues

  

3. retro：每次 session 结束做复盘，更新 Project.md 的"避免再犯"规则\

输出：每个命令的触发方式 + 输入输出约定。

  

**3) BUILD：Vibe Coding 开发提示词（3 种工作流）**

  

**B0：先做 MVP（强制 plan mode）**

  

你先进入 plan mode：把 Spec Doc

翻译成"可执行实现计划"，列步骤、文件改动点、风险。\

必须先问我 3 个澄清问题再写代码。\

然后只实现 MVP（Milestone 1），不允许偷跑到 V2/V3。

  

**B1：单功能通用流程（Research → Plan → Implement → Test）**

  

对这个功能：

  

1. Research：如果涉及新 API/库，先输出 1 页 research note

  

2. Plan：给出实现步骤+验收点

  

3. Implement：按步骤提交

  

4. Test：给出可运行测试/脚本/手动验收步骤\

最后执行 update-docs。

  

**B2：Issue-based（用 GitHub issues 做真源）**

  

以 GitHub issues 为任务入口：

  

- 每个 issue 必须有：背景/目标/验收标准/范围边界

  

- 你按 issue 开分支、实现、测试、写 PR 描述

  

- 完成后更新 changelog + status

  

**B3：多代理并行（高级）**

  

当我说"并行开发"时：

  

- 为每个 feature 建独立 worktree/分支

  

- 每个会话只处理自己的 issue

  

- 最后合并前先做冲突检查与回归测试\

输出：worktree 命令 + 合并策略建议

  

**4) 4 条"持续效率"硬提示词（建议放 PROJECT.md）**

  

**T1：用最强模型做最关键的事**

  

规划/复杂决策用最强模型；实现用稳定模型；简单修复用轻量模型。\

目标：减少返工时间，而不是省 token。

  

**T2：PROJECT.md 必须持续更新但不能膨胀**

  

每次新增规则/约束，只写一句"可执行约束"，并链接到详细文档。\

禁止把长篇讨论塞进 PROJECT.md。

  

**T3：回归预防（别只修 bug）**

  

当你犯错时：不要只修复。必须把"如何避免再犯"的一句规则写入

PROJECT.md（或由 retro 自动写）。

  

**T4：允许推翻重来**

  

原型阶段允许删掉重做。代码很便宜，时间最贵。\

优先保证 MVP 可验收，不要执着错误方向。
