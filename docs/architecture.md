# Architecture

最后更新：2026-04-03

## 当前架构状态

当前仓库已从“纯文档治理层”进入“文档 + 业务实现并行层”。现有结构可分为六层：

1. 规则源层
- `RAPA_Support_Documents/0-1 Vibe Coding 项目启动提示词包（PSB）.md`
- `RAPA_Support_Documents/ENGINEERING_RULES.md`

2. 执行与自动化层
- `Makefile`
- `scripts/`

3. 技能与资源层
- `skills/`
- `.skill-control/`

4. Phase 1 规格层
- `docs/project-brief.md`
- `docs/project-spec.md`
- `docs/skill-draft.md`
- `docs/skill-draft-guide.md`
- `docs/run-blueprint.md`
- `docs/eval-plan.md`

5. Phase 2 执行计划层
- `ENGINEERING_EXECUTION_PLAN.md`

6. 业务实现层
- `rednote-ads-placement-analyzer/`
- `rednote-ads-placement-analyzer/vendor/mediacrawler_xhs/`
- `rednote-ads-placement-analyzer/scripts/`
- `rednote-ads-placement-analyzer/assets/`
- `rednote-ads-placement-analyzer/evals/`
- `rednote-ads-placement-analyzer/runs/`

## 业务实现层

- 当前状态：`已进入 MVP 实现`
- 当前模块：
  - `SKILL.md`：最终产品入口与执行说明
  - `assets/standard_analysis_prompt.md`：标准分析 Prompt
  - `references/xhs-platform-context.md`：分析前置平台语境
  - `scripts/run_pipeline.py`：`prepare-run` / `crawl` / `finalize-broadcast`
  - `vendor/mediacrawler_xhs/`：内化后的 donor 小红书抓取主干与 run 级存储适配，现承担可信登录判别
  - `evals/`：主样本与边界样本夹具及期望
  - `runs/`：实际交付产物
- 约束：业务模块命名、目录边界、术语定义一旦落盘，后续不得随意漂移

## 当前登录与执行主链

- 登录意图只在首次环境装载完成后询问一次，避免把登录判断散落到抓取过程中
- donor 登录判别不再只依赖 `selfinfo`，而是采用“API 判别 + 页面登录态回退”的单一可信结论
- 用户若明确选择无登录，本次任务后续不再反复要求登录
- 用户若后续再次主动要求登录，必须对同一链接组重新执行任务并新建 run，不能续跑旧 run
- 无登录模式不阻塞抓取主链，但必须在单篇报告、综合报告与 `final_broadcast.md` 中显式披露评论完整度边界

## 文档分工

- `Project.md`：唯一入口、硬约束、索引
- `docs/status.md`：当前阶段、停靠点、下一步
- `docs/changelog.md`：变更摘要
- `docs/project-brief.md`：目标、用户、问题、MVP 边界
- `docs/project-spec.md`：产品流程、工程栈、模块、接口、约束
- `ENGINEERING_EXECUTION_PLAN.md`：MVP 工作包、执行顺序、依赖关系、DoD 与同步动作
- `docs/skill-draft.md`：接近最终版的 `SKILL.md` draft
- `docs/skill-draft-guide.md`：`skill-draft.md` 的撰写指导与约束来源
- `docs/run-blueprint.md`：run 目录、命名与落盘蓝图
- `docs/eval-plan.md`：首轮评估方案与验收标准
- `docs/feature-notes/*.md`：单功能规则、边界、特殊约束
- `rednote-ads-placement-analyzer/SKILL.md`：当前真实产品入口
- `docs/feature-notes/rednote-ads-placement-analyzer.md`：产品模块边界与验证记录

## 更新规则

- 新增业务模块时，在本文件登记模块职责、边界、依赖关系
- 修改数据流、目录结构或核心术语时，必须先更新本文件再继续扩展实现
- 如果某个功能有独立规则，新增对应 `docs/feature-notes/<feature>.md`
