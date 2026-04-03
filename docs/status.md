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
- 开始重构登录主链：从“产品层临时补丁”回收为“donor 可信登录判别 + 一次性登录决策 + 无登录风险披露”
- 修复 run 级评论落盘覆盖问题，评论批次现在会累积保存，不再只保留最后一批
- 使用标准 Prompt 对指定 3 条小红书样本完成 fresh run：生成 3 篇单篇标准结构报告、1 篇综合报告与最终播报，1 条抖音链接被排除
- 对另一组 3 条小红书样本完成 fresh run：生成 3 篇单篇标准结构报告、1 篇综合报告与最终播报；其中 1 条抖音链接被排除，1 篇样本未抓到评论文件但正文、图片与报告已完整落盘
- 对包含 1 条非小红书新闻链接的混合样本完成 fresh run：生成 3 篇单篇标准结构报告、1 篇综合报告与最终播报，头条链接被正确排除

## 当前已知事实

- 项目当前定位仍为“内部研究原型”
- 当前真实产品目录已落地到 `rednote-ads-placement-analyzer/`
- 系统自带 Python 依赖不全；当前可用抓取环境是 `skills/MediaCrawler/.venv/bin/python`
- 匿名 fallback 模式下，单链接样本可成功拿到正文、图片、评论、互动数据与词云图
- 匿名 fallback 模式下，多链接样本也可完成完整 run 交付；评论子回复仍可能部分失败，但不会阻断整条 run
- 评论接口在部分运行中仍可能触发验证码；当前策略是保留已成功资产，不因部分失败丢弃整条 run
- 当前设备环境中“页面已登录”与 `selfinfo` 返回成功不是同一个口径；donor 登录判别需要引入页面登录态回退，不能再只看 `selfinfo`
- `source_prompt_mode=standard` 的 fresh run 已验证可完整落地标准 Prompt 要求的单篇/综合报告结构与最终播报
- mixed samples 下仍会出现评论子回复 `DataFetchError / RetryError`；当前不会阻断整条 run，但部分样本可能只落正文、图片与互动数据
- 当前环境下部分 fresh run 会把标准 Prompt 正文写入 `explicit_instruction`，但 `source_prompt_mode` 仍显示为 `run-specific`；不影响报告结构落地

## 当前阻塞 / 待确认

- 抓取稳定性仍受小红书验证码与环境状态影响
- 标准 Prompt 报告已验证可生成，但目前仍依赖会话内分析落档，尚未产品化为独立脚本步骤

## 下一步

1. 用更多 mixed samples 继续回归，覆盖登录态差异、非法链接排除与评论子回复失败边界
2. 将单篇报告与综合报告生成产品化，减少会话内人工落档步骤
3. 继续验证 donor 登录判别在真实已登录环境下的稳定性
4. 评估是否需要把评论子回复失败计数写入 run manifest 或最终播报

## 上次停靠点

- 当前已完成一条 `source_prompt_mode=standard` 的 fresh run 闭环验证；下一步优先推进报告生成产品化与更多样本回归
