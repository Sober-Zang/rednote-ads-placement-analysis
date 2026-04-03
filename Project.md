# Project.md

本仓库统一使用 `Project.md` 作为唯一项目入口与持久化索引。不要再新增 `Agent.md`、`Memory.md` 等同义文件。

## 当前状态

- 项目名称：`rednote-ads-placement-analysis`
- 当前阶段：`Phase 2` MVP 工程实现与验证
- 当前主线：在根级 `rednote-ads-placement-analyzer/` 下完成真实产品目录、执行脚本、内化 donor 抓取层与 run 级交付闭环
- 当前事实：产品骨架、`SKILL.md`、标准 Prompt、执行脚本、eval 配置和 donor 适配层已落盘；已验证一条单链接 run 可完成抓取、归档、单篇报告与最终播报

## 入场必读

每次新会话都按这个顺序读取，不跳步：

1. `Project.md`
2. `docs/status.md`
3. 按需下钻：`docs/architecture.md`、`docs/project-brief.md`、`docs/project-spec.md`
4. 若涉及规则冲突，再回看 `RAPA_Support_Documents/ENGINEERING_RULES.md`

## 工作主约束

- 任何功能必须遵守 `Research -> Plan -> Implement -> Test & Sync`，禁止跳过规划直接写代码。
- 当前阶段严格冻结在已确认 Milestone 内，未确认需求一律进入 Backlog。
- `RAPA_Support_Documents/Original_Prompt.md` 是不可变源文件，任何阶段都不得改写。
- `Project.md` 只保留必须知道的硬约束和索引，不写流水账，不灌入大段实现细节。
- 每次任务完成后，至少同步 `docs/status.md` 与 `docs/changelog.md`。
- 任何会影响模块边界、数据流或术语定义的变更，必须同步更新 `docs/architecture.md` 与对应 `docs/feature-notes/`。
- 如果出现严重错误或范围漂移，先修正代码/文档，再把防复发规则抽象成一句硬规则回写到本文件。
- 禁止直接向 `main` 推送；后续开发遵循 `main + feature branch`。
- `skill-creator` 在本项目中默认保持 `enabled`，除非用户明确要求禁用。
- 若后续进入 UI/Web 开发，会话内优先使用开发服务器，避免执行破坏调试状态的生产构建。
- 当小红书抓取在评论或媒体阶段遇到环境验证码/反爬阻塞时，必须保留已成功落盘的 run 资产并显式标记缺口，不能因为部分失败而丢弃整条 run。

## 当前仓库概览

- `RAPA_Support_Documents/`：项目启动规则与工程约束原文
- `docs/`：项目事实层与持续同步层
- `scripts/`：项目自动化脚本
- `skills/`：技能相关资产
- `rednote-ads-placement-analyzer/`：当前 MVP 产品目录与运行产物
- `Makefile`：常用命令入口

## 文档更新循环

开始任务前：

- 先在 `docs/status.md` 明确当前目标、范围、停靠点和下一步。

完成任务后：

- 在 `docs/changelog.md` 记录变更摘要。
- 在 `docs/status.md` 更新当前状态、阻塞项、下一步。
- 若架构或功能边界有变化，同步更新 `docs/architecture.md` 与对应 `docs/feature-notes/`。
- 若发现新的防呆规则，只追加一句规则到 `Project.md`，不要写成长文。

## 常用命令

- `make verify-skill`
- `make skill-status`
- `make skill-enable`
- `make skill-disable`
- `make build CMD="<your command>"`

## 链接清单

- [项目简报](docs/project-brief.md)
- [项目规格](docs/project-spec.md)
- [工程执行计划](ENGINEERING_EXECUTION_PLAN.md)
- [产品目录](rednote-ads-placement-analyzer/SKILL.md)
- [Skill 草案](docs/skill-draft.md)
- [Skill Draft 指南](docs/skill-draft-guide.md)
- [Run 蓝图](docs/run-blueprint.md)
- [评估计划](docs/eval-plan.md)
- [当前状态](docs/status.md)
- [架构文档](docs/architecture.md)
- [变更记录](docs/changelog.md)
- [功能笔记模板](docs/feature-notes/_template.md)
- [产品功能笔记](docs/feature-notes/rednote-ads-placement-analyzer.md)
- [原始目标提示](RAPA_Support_Documents/Original_Prompt.md)
- [启动提示词包](RAPA_Support_Documents/0-1%20Vibe%20Coding%20项目启动提示词包（PSB）.md)
- [工程规则](RAPA_Support_Documents/ENGINEERING_RULES.md)
