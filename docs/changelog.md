# Changelog

## 2026-04-02

- 新增根级 `Project.md`，并统一其为本项目唯一入口与持久化索引
- 新增 `docs/status.md`、`docs/architecture.md`、`docs/project-brief.md`、`docs/project-spec.md`
- 新增 `docs/feature-notes/_template.md`，用于后续功能边界记录
- 固化文档同步节奏：任务完成后必须回写状态、变更、架构与功能笔记

## 2026-04-03

- 将 `RAPA_Support_Documents/Original_Prompt.md` 明确登记为不可变源文件
- 将 `docs/project-brief.md` 从模板补全为内部研究原型的正式简报
- 将 `docs/project-spec.md` 从模板补全为产品与工程合一的正式规格
- 新增 `docs/skill-draft.md`，锁定未来 `SKILL.md` 的结构、触发规则和五阶段流程
- 新增 `docs/run-blueprint.md`，锁定 run 命名、目录、落盘与引用规则
- 新增 `docs/eval-plan.md`，锁定首轮测试 Prompt、验收标准与评估边界
- 更新 `Project.md`、`docs/status.md`、`docs/architecture.md` 以反映 Phase 1 已完成
- 将旧 `docs/skill-draft.md` 原样改名为 `docs/skill-draft-guide.md`
- 新建新的 `docs/skill-draft.md`，重写为接近最终版的 `SKILL.md` draft
- 将 `docs/eval-plan.md` 重写为“主检验样本 + 补充边界场景”的结构
- 修复重命名后直接受影响的索引引用

## 2026-04-04

- 新增 `ENGINEERING_EXECUTION_PLAN.md`，将 MVP 工程落地拆解为工作包级执行计划
- 在执行计划中明确文档优先级、入场顺序、冲突裁决顺序、工作包依赖关系与 DoD
- 更新 `Project.md` 以反映项目已进入 Phase 2 MVP 工程执行规划
- 更新 `docs/status.md`、`docs/architecture.md` 以纳入工程执行计划层

## 2026-04-03

- 新建根级产品目录 `rednote-ads-placement-analyzer/`
- 内化 donor 小红书抓取主干到 `rednote-ads-placement-analyzer/vendor/mediacrawler_xhs/`
- 新增正式 `rednote-ads-placement-analyzer/SKILL.md`
- 新增标准 Prompt 资产、平台语境参考、执行脚本与 `evals/evals.json`
- 实现 `prepare-run`、`crawl`、`finalize-broadcast` 三段式执行链路
- 将 donor 默认数据库存储改造成 run 级 JSON / JPG / reference index 落盘
- 验证单链接真实样本可完成抓取、归档、单篇报告与最终播报
- 修复 `run_pipeline.py` 登录态探测在首页访问超时后直接终止 run 的问题，改为可降级到无登录继续抓取
- 验证一组混合输入可完成多样本闭环：4 个小红书链接成功抓取并产出单篇/综合报告，1 个抖音链接被正确排除
- 新增 `docs/feature-notes/rednote-ads-placement-analyzer.md`
- 更新 `Project.md`、`docs/status.md`、`docs/architecture.md` 以反映已进入 MVP 实现与验证阶段
