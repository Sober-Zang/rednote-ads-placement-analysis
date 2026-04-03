# Status

最后更新：2026-04-03

## 当前阶段

- 阶段：`Phase 2` MVP 工程实现与验证
- 主线：在 `rednote-ads-placement-analyzer/` 下完成真实产品目录、执行脚本、抓取适配层与 run 级交付闭环
- 范围冻结：当前只推进 MVP，不展开 V2/V3

## 本次已完成

- 复核 `skill-creator` 当前仍为 `enabled`
- 在根级新建 `rednote-ads-placement-analyzer/` 产品目录
- 内化 donor 小红书抓取主干到 `vendor/mediacrawler_xhs/`
- 新建正式 `SKILL.md`、标准 Prompt 资产、平台语境参考、执行脚本与 `evals/evals.json`
- 实现 `prepare-run`、`crawl`、`finalize-broadcast` 三段式执行链路
- 跑通一条真实单链接样本：完成 run 建立、图文/图片/评论/互动数据落盘、reference index、单篇分析报告与最终播报
- 跑通一组真实多样本输入：4 个小红书链接完成抓取、单篇报告、综合报告与最终播报，1 个抖音链接被正确排除
- 修复登录态探测在首页 `goto` 超时时直接终止整条 run 的问题，现可降级为无登录继续抓取
- 验证边界场景：
  - `0` 有效链接时停止在准备阶段
  - run 专属 Prompt 只写入当前 run，不污染全局资产

## 当前已知事实

- 项目当前定位仍为“内部研究原型”
- 当前真实产品目录已落地到 `rednote-ads-placement-analyzer/`
- 系统自带 Python 依赖不全；当前可用抓取环境是 `skills/MediaCrawler/.venv/bin/python`
- 匿名 fallback 模式下，单链接样本可成功拿到正文、图片、评论、互动数据与词云图
- 匿名 fallback 模式下，多链接样本也可完成完整 run 交付；评论子回复仍可能部分失败，但不会阻断整条 run
- 评论接口在部分运行中仍可能触发验证码；当前策略是保留已成功资产，不因部分失败丢弃整条 run

## 当前阻塞 / 待确认

- 抓取稳定性仍受小红书验证码与环境状态影响
- 综合报告已验证可生成，但目前仍依赖会话内分析落档，尚未产品化为独立脚本步骤

## 下一步

1. 将单篇报告与综合报告生成进一步产品化，减少人工落档步骤
2. 针对评论接口验证码和媒体下载波动继续提升抓取稳定性
3. 补充多样本回归用例，覆盖非小红书链接混入与无登录降级路径
4. 每次修正后立即同步状态、变更、架构与 feature note

## 上次停靠点

- 当前仓库已具备真实多样本闭环，能在无登录条件下完成 4 链小红书样本 + 1 条非小红书链接排除的 run 交付
- 下一个会话应从 `Project.md -> docs/status.md -> rednote-ads-placement-analyzer/SKILL.md -> ENGINEERING_EXECUTION_PLAN.md` 顺序继续，并优先推进报告生成产品化
