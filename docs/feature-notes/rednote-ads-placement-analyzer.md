# Rednote Ads Placement Analyzer

## 功能名

- `rednote-ads-placement-analyzer`

## 所属里程碑

- MVP

## 目标

- 在仓库根级建立真实可用的 Agent Skill 产品目录
- 将小红书链接解析、run 初始化、数据抓取、证据归档、单篇/综合报告落盘与最终播报串成一条可复核闭环

## In Scope

- `SKILL.md` 正式版
- 标准 Prompt 资产与小红书平台语境参考
- `prepare-run` / `crawl` / `finalize-broadcast` 执行脚本
- donor 小红书抓取主干的内化与 run 级存储适配
- `evals/evals.json` 与主样本/边界样本夹具

## Out of Scope

- Web UI
- 云端部署
- 多平台扩展
- 商业化合规替代方案
- 全自动多样本报告生成评测流水线

## 关键规则与边界

- 最终用户可见的 `SKILL.md` 不暴露任何外部 skill 部署叙事
- 标准 Prompt 只存于全局 `assets/`；run 专属 Prompt 只能进入当前 run
- donor 代码只读保留在 `skills/MediaCrawler/`，最终运行入口在 `rednote-ads-placement-analyzer/`
- 评论或媒体抓取若受验证码/环境限制阻塞，保留已抓到的 run 资产，不得整 run 丢弃

## 依赖与影响面

- 依赖 `playwright`、`httpx`、`aiofiles`、`humps`、`tenacity`
- 词云图依赖 `jieba`、`wordcloud`、`PIL`
- 当前本地验证使用 `skills/MediaCrawler/.venv/bin/python`
- 影响文档：`Project.md`、`docs/status.md`、`docs/architecture.md`、`docs/changelog.md`

## 验收标准

- 能从混合文本中提取候选链接并筛出 `xhslink.com`
- 能建立 run 目录并落盘 `raw_user_input.md`、`link_manifest.json`、`invalid_links.md`、`used_prompt.md`
- 能完成至少一条真实单链接抓取并生成 `note_manifest.json`、`reference_index.json`
- 能生成单篇分析报告并写出 `final_broadcast.md`
- 边界场景覆盖 `0` 有效链接和 run 专属 Prompt

## 测试与验证

- 已验证：
  - `prepare-run` 主样本可识别 5 个小红书链接和 1 个 GitHub 链接
  - 单链接样本可完成真实抓取、图片落盘、评论落盘、词云图生成、单篇报告与最终播报
  - `0` 有效链接时返回非零退出码并停在准备阶段
  - 自定义 Prompt 只写入当前 run，不进入全局 `assets/`
- 当前剩余：
  - 5 链主样本尚未完整跑通到综合报告
  - 评论接口在部分运行环境下仍可能触发验证码，需要继续优化稳定性
