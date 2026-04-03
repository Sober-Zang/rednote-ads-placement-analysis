---
name: rednote-ads-placement-analyzer
description: >
  面向小红书广告投放研究场景的一站式分析产品。它能从自然语言中提取多个小红书分享链接，
  将每个样本的图文、图片、评论、互动信息和辅助元数据整理到独立 run 目录，再基于标准分析 Prompt
  生成逐篇分析与跨样本综合结论，帮助团队解释为什么这些内容更容易获得高 ROI / 高 CVR，并沉淀可复核的方法论。
  当任务涉及小红书链接解析、优质样本拆解、广告投放潜力分析、共性机制总结、run 级证据归档时，应优先使用本 skill。
---

# Rednote Ads Placement Analyzer

用于把多个小红书图文样本从“混杂输入”推进到“结构化证据 + 单篇报告 + 综合报告 + run 级可复核交付”。

## 安装部署

### 系统要求

- Python 3.11+
- Playwright 可用
- 足够的本地磁盘空间
- 可用的小红书访问环境

### 目录结构

```text
rednote-ads-placement-analyzer/
  SKILL.md
  assets/
  references/
  scripts/
  vendor/
  evals/
  runs/
```

### 核心脚本

| 脚本 | 作用 | 何时使用 |
|------|------|----------|
| `scripts/check_environment.py` | 检查当前 Python 环境是否具备抓取依赖 | 首次使用或环境报错时 |
| `scripts/run_pipeline.py prepare-run` | 提取链接、建立 run 目录、写入 Prompt 和输入清单 | 每次新任务开始时 |
| `scripts/run_pipeline.py crawl` | 触发内置小红书采集引擎并落盘原始材料 | `prepare-run` 成功后 |
| `scripts/run_pipeline.py finalize-broadcast` | 汇总报告路径并生成最终播报 | 报告写完后 |

## 环境验证

先检查 skill 状态与 Python 依赖：

```bash
make skill-status
python3 rednote-ads-placement-analyzer/scripts/check_environment.py
```

最低通过标准：

- `skill-creator` 处于 `enabled`
- 当前 Python 环境具备 `playwright`、`httpx`、`aiofiles`、`humps`、`tenacity`
- 若要生成词云图，还需具备 `jieba`、`wordcloud`、`PIL`

## 首次使用设置

首次进入任务时，先确定：

1. 本次用户输入的原始文本是否需要保存到新的 run
2. 本次任务是否只使用标准 Prompt
3. 当前运行环境是否足以执行抓取

如果当前 Python 缺少依赖，不要硬跑 `crawl`；先换到可用环境，再继续执行。

## 工作流程（5 阶段）

> 你必须严格按顺序执行，不要跳阶段，不要把不同 run 的材料混在一起。

### 阶段 1：输入检查与链接提取

目标：从用户自然语言中提取候选链接，识别有效小红书链接，并初始化 run。

执行：

```bash
python3 rednote-ads-placement-analyzer/scripts/run_pipeline.py prepare-run \
  --input-file /absolute/path/to/raw_user_input.txt
```

如果用户有额外提示词，改用：

```bash
python3 rednote-ads-placement-analyzer/scripts/run_pipeline.py prepare-run \
  --input-file /absolute/path/to/raw_user_input.txt \
  --custom-prompt-file /absolute/path/to/custom_prompt.md
```

检查点：

- 只把 `xhslink.com` 链接纳入后续分析
- 非小红书链接必须被写入 `inputs/invalid_links.md`
- 有效链接数为 `0` 时立即停止，不进入抓取
- `prompt/used_prompt.md` 必须存在

### 阶段 2：小红书数据下载与整理

目标：为每个有效链接下载图文、图片、评论、互动信息和辅助元数据，并按 run 规则整理。

登录状态规则：

- 执行抓取前先检查当前环境是否具备有效登录状态。
- 若缺失登录信息，必须提示用户：未登录可能导致评论区内容抓取不全或只能拿到有限信息。
- 随后给用户 30 秒确认，并提供两个选项：
  - 现在登录后再继续
  - 不登录，直接继续
- 若用户 30 秒内明确选择“不登录”，或 30 秒内没有任何回应，则直接按无登录条件继续后续步骤。
- 若用户 30 秒内明确选择“现在登录后再继续”，则进入 5 分钟登录窗口。
- 在这 5 分钟内，持续检测登录态是否已恢复，同时明确提示用户仍然可以随时打断等待、直接继续无登录工作。
- 该提示必须包含：若不需要打断，则无需回复；完成登录后请等待自动进行后续工作。
- 若 5 分钟内检测到登录成功，则立即转入后续有登录条件下的抓取流程。
- 若 5 分钟内用户主动要求不再等待，则立即结束等待，并按无登录条件继续。
- 若 5 分钟结束仍未登录成功，则重新回到“30 秒确认是否要登录”的步骤循环询问。

执行：

```bash
python3 rednote-ads-placement-analyzer/scripts/run_pipeline.py crawl \
  --run-dir /absolute/path/to/rednote-ads-placement-analyzer/runs/<run_id>
```

检查点：

- 每个有效链接最终都要落到独立样本目录
- 目录展示语义是“完整标题 + 作者昵称”
- 至少要有：
  - `raw/note.json`
  - `raw/note_text.md`
  - `raw/comments.json`
  - `raw/metrics.json`
  - `images/`
  - `manifests/note_manifest.json`
  - `manifests/reference_index.json`
- 如果可用，保留词云图与视频文件

### 阶段 3：Prompt 选择与 run 级资产准备

目标：确认本次 run 使用标准 Prompt 还是 run 专属 Prompt，并把证据索引准备好。

规则：

- 仅当用户没有额外要求，或额外要求与标准任务严格等价时，使用 `assets/standard_analysis_prompt.md`
- 否则只能使用当前 run 内的 `prompt/used_prompt.md`
- 专属 Prompt 绝不能写回 `assets/`
- 分析前先读取：
  - `prompt/used_prompt.md`
  - `references/xhs-platform-context.md`
  - 每个样本目录下的 `manifests/reference_index.json`

### 阶段 4：单篇分析与综合分析

目标：按标准 Prompt 或 run 专属 Prompt 写出单篇报告，再在多样本场景下写综合报告。

分析前必须先建立这个平台视角：

- 小红书用户更看重真实感、经验感、生活化表达、细节证据和“我也能做到”的可复制感
- 高转化内容依赖标题钩子、首图吸引、正文解释、评论补强共同作用
- 你的判断必须解释“为什么它在小红书语境里更容易被信任、被收藏、被讨论、被转化”

单篇报告要求：

- 路径：`notes/<sample>/analysis/<图文标题+作者名>_分析报告.md`
- 先写一段简短的小红书平台语境说明
- 必须覆盖：
  - 文本
  - 图片
  - 评论
  - 互动数据
  - 关联机制
  - 投放潜力
  - 可复用方法
  - 风险边界
- 所有关键结论带引用标签

综合报告要求：

- 多于 1 个有效样本时才生成
- 路径：`aggregate/<本次总结出的共有特点+时间戳>_综合分析报告.md`
- 只能基于本次 run 的单篇报告，不要混入历史 run

### 阶段 5：最终落档与播报

目标：让用户能直接定位本次 run 的全部产物。

报告写完后执行：

```bash
python3 rednote-ads-placement-analyzer/scripts/run_pipeline.py finalize-broadcast \
  --run-dir /absolute/path/to/rednote-ads-placement-analyzer/runs/<run_id>
```

必须确认：

- `logs/final_broadcast.md` 已生成
- `run_manifest.json` 已写入报告输出路径
- 最终播报里明确列出被排除的非小红书链接

## 完成后输出

典型输出结构：

```text
runs/
  run_<timestamp>_<task-slug>/
    manifests/
      run_manifest.json
      link_manifest.json
    prompt/
      used_prompt.md
      prompt_mode.json
    inputs/
      raw_user_input.md
      invalid_links.md
    notes/
      01_<标题>__<作者>/
        raw/
        images/
        assets/
        analysis/
        manifests/
    aggregate/
      <共有特点+时间戳>_综合分析报告.md
    logs/
      final_broadcast.md
```

## 参考文件

- 标准分析 Prompt：`assets/standard_analysis_prompt.md`
- 小红书平台语境：`references/xhs-platform-context.md`
- 运行校验：`scripts/check_environment.py`

## 执行提醒

- 不要在用户可见文本中提及任何外部 skill、外部部署或 donor 工程名称
- 不要修改全局标准 Prompt 来适配单次任务
- 不要跳过 `reference_index.json` 直接下判断
- 报告质量不够时，优先回到证据与 Prompt，而不是写空泛长文
- 若抓取环境不满足或需要人工登录，不要伪装成已完成抓取
