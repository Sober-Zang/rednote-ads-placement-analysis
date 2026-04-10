---
name: rednote-ads-placement-analyzer
description: >
  面向小红书广告投放研究场景的一站式分析产品。它能从自然语言中提取多个小红书分享链接，
  将每个样本的图文、图片、评论、互动信息和辅助元数据整理到官方 run 目录，再为逐篇分析与跨样本综合结论准备可复核证据。
  它适合处理链接解析、优质样本拆解、广告投放潜力分析、共性机制总结、run 级证据归档等任务。
---

# Rednote Ads Placement Analyzer

用于把多个小红书图文样本从“混杂输入”推进到“结构化证据 + 可复核交付”的产品化执行流水线。

## 核心规则

- 默认把仓库源码视为只读，不要把正常运行副作用写回仓库。
- 官方 run 产物只能写入 `OUTPUT_DIR`。
- 默认不再生成单独的 sibling `RUNTIME_DIR`；短生命周期运行态应跟随当前 run 写入 `OUTPUT_DIR`。
- 临时文件只允许写入当前官方 run 或系统临时目录。
- 默认每次都重新完整执行任务；只有用户明确允许时才复用旧 run。
- 只使用官方入口 `pipeline.py`。

## 仓库主面

```text
repo/
  pipeline.py
  requirements-execution.txt
  README.machine.md
  docs/contracts/
  rednote-ads-placement-analyzer/
    assets/
    evals/
    references/
    scripts/
    vendor/
```

真实输出和浏览器状态不属于仓库内容。

## 安装部署

### 系统要求

- Python 3.11+
- Playwright 可用
- 足够的本地磁盘空间
- 可用的小红书访问环境

### 环境准备

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-execution.txt
python -m playwright install chromium
```

Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-execution.txt
python -m playwright install chromium
```

## 默认外部目录

如果没有显式设置环境变量，默认使用与项目目录同级的显式目录：

- `../rednote-ads-placement-analysis-output`

macOS / Linux:

```bash
export OUTPUT_DIR="/absolute/path/to/rednote-ads-placement-analysis-output"
```

Windows PowerShell:

```powershell
$env:OUTPUT_DIR="D:\path\to\rednote-ads-placement-analysis-output"
```

要求：

- `OUTPUT_DIR` 必须在仓库外
- 不再默认生成单独的 sibling `RUNTIME_DIR`
- 后续执行只能使用这套固定显式目录，不允许自行乱建新目录
- 为了提高当前设备上的登录态复用率，仓库根目录下允许保留唯一一个例外目录：`xhs_user_data_dir/`
- 这个例外只服务于小红书登录态复用，项目中其他已有内容都不允许被运行时写回

## 环境验证

先检查当前 Python 依赖和外部目录边界：

macOS / Linux:

```bash
python pipeline.py check-env
```

Windows PowerShell:

```powershell
python pipeline.py check-env
```

最低通过标准：

- 当前 Python 环境具备 `playwright`、`httpx`、`aiofiles`、`pyhumps`、`tenacity`
- 具备 `PIL`、`jieba`、`wordcloud`、`numpy`、`matplotlib`
- 当前解释器位于仓库根目录下的 `.venv`
- `OUTPUT_DIR` 位于仓库外
- 不再依赖单独的 sibling `RUNTIME_DIR`

## 工作流程（5 阶段）

> 你必须按顺序执行，不要跳阶段，不要把不同 run 的材料混在一起。

### 阶段 1：输入检查与链接提取

目标：从用户自然语言中提取候选链接，识别有效小红书链接，并初始化官方 run。

执行：

```bash
python pipeline.py prepare-run --input-text "<用户原始输入全文>"
```

检查点：

- 只把 `xhslink.com` 链接纳入后续抓取
- 非小红书链接必须写入 `inputs/invalid_links.md`
- 有效链接数为 `0` 时立即停止，不进入抓取
- `prompt/used_prompt.md` 必须存在
- 如果用户给出了与标准任务不完全一致的额外任务提示词，则为本次 run 生成 run 专属 Prompt，并且只能写入当前 run
- 如果没有小红书链接且只存在 run 专属 Prompt，则直接围绕该 Prompt 回答，不执行抓取
- 不要自行创建 `task_input.md`、`m+ task_input.md` 等临时文件名；机器执行优先用 `--input-text`

### 阶段 2：登录状态检测

目标：在抓取前检测当前小红书是否已完成登录；当用户只要求登录时，只执行这一阶段。

规则：

- 先自动打开受控 Chrome 并检查当前是否已经登录
- 若已经登录，直接继续后续任务
- 若尚未登录，则先自动清空失效的 `xhs_user_data_dir`，再保持 Chrome 打开并给 300 秒等待用户登录
- 提示用户：未登录不会阻塞任务，但评论区、二级评论和评论图片区可能不完整；如果不需要登录，直接关闭浏览器即可，系统会按无登录流程继续
- 一旦进入 300 秒等待窗口，就不要因为中途某次探测失败而提前结束；应给足完整等待时间
- 若 300 秒窗口结束时已确认登录成功，则进入登录态继续执行
- 若超时或浏览器被关闭，则回落为无登录模式继续执行
- 若用户后续再次主动提出希望登录账号，不要复用之前无登录的结果；应对同一组链接重新执行任务，重新建立 run
- 若用户单独提出“我要登录小红书账号”或同类诉求，则只执行本阶段：不建立 run，不抓取，不分析，不生成输出产物

### 阶段 3：小红书数据下载与整理

目标：把每个有效链接下载成官方 run 结构。

执行：

```bash
python pipeline.py crawl --run-dir "$OUTPUT_DIR/run_<timestamp>_<task-slug>"
```

检查点：

- 每个有效链接都要落到独立样本目录
- 官方 manifest 必须只保留 run 相对路径
- 至少保留：
  - `raw/note.json`
  - `raw/note_text.md`
  - `raw/comments.json`
  - `raw/metrics.json`
  - `images/`
  - `manifests/note_manifest.json`
  - `manifests/reference_index.json`
- 单篇帖子评论总抓取上限为 `500`
- 二级评论抓取的完整度直接受登录态影响；应先等待登录状态明确，再开始抓取，而不是边登录边抓
- 二级评论抓取失败只应表现为当前根评论降级，不应直接打崩整条 run

### 阶段 4：分析准备

目标：在标准任务下尽最大可能产出单篇分析和综合分析；在自定义任务下切换到 run 专属 Prompt。

规则：

- 当前 run 只使用 `prompt/used_prompt.md`
- 分析前应读取每个样本目录内的证据文件和 `reference_index.json`
- 图片必须真实提供给模型阅读和思考，尤其是关键正文图片
- 如果某张图没有成功提供给模型，不要假装已经看过，也不要据此得出肯定结论
- 若本次是标准任务：
  - 对每个成功下载并具备足够证据的样本生成单篇报告
  - 只基于成功生成单篇报告的样本生成综合报告
  - 若 3 条有效链接里有 1 条下载失败，则仍要对其余成功样本继续生成单篇报告和综合报告
  - 不要只下载和广播；标准任务应把“报告产出”视为默认目标，尽最大可能完成单篇报告与综合报告
- 若本次是自定义任务且同时包含小红书链接：
  - 先完成下载与归档
  - 再改用本次 run 的专属 Prompt 回答用户指定目标
  - 这类回答不必强制固化成 `final_broadcast.md`

### 阶段 5：最终落档与契约校验

目标：在标准任务下完成最终播报与契约校验；若报告无法生成，必须在播报中明确说明原因。

执行：

```bash
python pipeline.py finalize-broadcast --run-dir "$OUTPUT_DIR/run_<timestamp>_<task-slug>"
python pipeline.py validate-contract --run-dir "$OUTPUT_DIR/run_<timestamp>_<task-slug>"
```

必须确认：

- `logs/final_broadcast.md` 已生成
- 标准任务下，对话输出必须与 `logs/final_broadcast.md` 完全一致
- 若分析报告尚未生成，播报必须明确说明当前状态与原因
- 契约校验通过
- 不要发明额外输入输出文件名
- 若 run 内存在人工补充材料，如表格或人工整理结果，应跟随当前 run 存放在 `manual-artifacts/` 下，而不是漂浮到 `OUTPUT_DIR` 根目录

## 官方输出契约摘要

每个官方 run 至少必须包含：

- `inputs/raw_user_input.md`
- `inputs/invalid_links.md`
- `manifests/link_manifest.json`
- `manifests/run_manifest.json`
- `prompt/used_prompt.md`
- `prompt/prompt_mode.json`

明确禁止的非契约文件名：

- `raw_user_input.txt`
- `used_prompt.txt`
- `link_manifest.txt`
- `run_manifest.txt`

## 参考文件

- [README（机器版）](../README.machine.md)
- [Execution-Only Contract](../docs/contracts/execution-only.md)
- [Output Contract](../docs/contracts/output-structure.md)
- [Runtime Contract](../docs/contracts/runtime-state.md)
- [XHS Platform Context](./references/xhs-platform-context.md)
