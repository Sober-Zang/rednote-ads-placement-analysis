# Rednote Ads Placement Analyzer 机器执行说明

面向小红书广告投放研究场景的一站式分析产品仓库。它能从自然语言里提取多个小红书分享链接，把每个样本的图文、图片、评论、互动信息和辅助元数据整理到独立 run 目录，并为后续单篇分析和跨样本综合分析准备可复核证据，帮助团队更稳定地复盘高 ROI / 高 CVR 内容为什么成立。

## 这个仓库是什么

这个仓库默认服务于**执行交付**，而不是开放式编码任务。

它的职责是：

- 从混杂文本中提取有效小红书链接
- 按固定契约生成 run 目录
- 下载帖子正文、图片、评论和辅助元数据
- 把分析所需的输入材料整理成稳定、可复核的结构

它被设计成：

- 仓库内只保留源码与文档
- 真实产物写到仓库外
- 浏览器登录态与运行期临时状态按固定规则收口
- 后续 AI 不需要猜路径、猜解释器、猜输入输出文件名

## 产品边界

| 层级 | 作用 | 写入规则 |
| --- | --- | --- |
| `rednote-ads-placement-analyzer/` | 产品源码、脚本、资产、vendor 子树 | 正常执行时只读 |
| `docs/contracts/` | 执行契约、输出契约、runtime 契约 | 正常执行时只读 |
| `OUTPUT_DIR/` | 正式 run 产物，以及 run 内临时文件 | 可写 |
| `xhs_user_data_dir/` | 小红书登录态长期复用目录 | 可写 |
| `/tmp/` | 仅限极短生命周期临时文件 | 可写 |

默认情况下，每次任务都应重新完整执行。只有用户明确允许时，才可复用历史 run。

## 官方入口

唯一推荐入口：

```bash
python pipeline.py <command> ...
```

官方命令：

| 命令 | 作用 |
| --- | --- |
| `check-env` | 检查 Python 依赖和外部目录边界 |
| `login-only` | 只执行登录检测与登录等待，不建立 run |
| `prepare-run` | 提取链接、建立新 run、写入官方输入材料 |
| `crawl` | 下载帖子正文、图片、评论和元数据 |
| `finalize-broadcast` | 生成官方最终播报文件 |
| `validate-contract` | 检查 run 结构与契约一致性 |

## 环境准备

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-execution.txt
python -m playwright install chromium
```

### Windows PowerShell

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-execution.txt
python -m playwright install chromium
```

## 默认外部目录

如果没有显式设置环境变量，流水线默认使用与项目目录同级的显式外部目录：

- `../rednote-ads-placement-analysis-output`

也可以手动设置：

### macOS / Linux

```bash
export OUTPUT_DIR="/absolute/path/to/rednote-ads-placement-analysis-output"
```

### Windows PowerShell

```powershell
$env:OUTPUT_DIR="D:\path\to\rednote-ads-placement-analysis-output"
```

规则：

- `OUTPUT_DIR` 必须在仓库外
- 不再默认生成单独的 sibling `RUNTIME_DIR`
- run 内短生命周期文件默认跟随当前 run 写入 `OUTPUT_DIR/run_*/`
- 不允许再使用主目录下的隐藏外部目录作为默认位置
- 为了提高当前设备上的小红书登录态复用率，仓库根目录下允许保留唯一一个例外目录：`xhs_user_data_dir/`
- 这个目录只用于复用小红书登录态；除它之外，项目中其他已有内容都不允许被运行态写回或污染

## 官方执行流程

```bash
python pipeline.py check-env
python pipeline.py prepare-run --input-text "<用户原始输入全文>"
python pipeline.py crawl --run-dir "$OUTPUT_DIR/run_<timestamp>_<task-slug>"
python pipeline.py finalize-broadcast --run-dir "$OUTPUT_DIR/run_<timestamp>_<task-slug>"
python pipeline.py validate-contract --run-dir "$OUTPUT_DIR/run_<timestamp>_<task-slug>"
```

补充入口：

```bash
python pipeline.py login-only
```

规则：

- `check-env` 是唯一前置硬门，未通过时不得继续后续步骤
- 机器执行优先使用 `--input-text`，不要自行发明 `task_input.md`、`m+ task_input.md` 等临时文件名
- 若必须落临时文件，只能写到当前 run 的官方目录内，不能写回仓库

## 官方 run 结构

```text
OUTPUT_DIR/
  run_<timestamp>_<task-slug>/
    aggregate/
    creators/
    inputs/
      invalid_links.md
      raw_user_input.md
    logs/
      final_broadcast.md
    manual-artifacts/
    manifests/
      link_manifest.json
      run_manifest.json
    notes/
    prompt/
      prompt_mode.json
      used_prompt.md
```

不要生成下列替代文件名：

- `raw_user_input.txt`
- `used_prompt.txt`
- `link_manifest.txt`
- `run_manifest.txt`

## 评论抓取规则

- 单篇帖子评论总抓取上限为 `500`
- 上限包含一级评论与二级评论总和
- 二级评论抓取失败不应直接打崩整条 run
- 达到上限应视为受控截断，而不是抓取失败

## 公开仓库主面

适合进入 public 主面的内容：

- execution-only 所需源码
- 官方入口
- 契约文档
- 最小 eval / fixture
- 必要资产与 vendor 子树

不应进入 public 主面的内容：

- 真实 runs
- 浏览器 profile
- cookie
- 本地虚拟环境
- 缓存
- 本机状态
- 内部工程背景材料

## 契约文档

- [Execution-Only Contract](./docs/contracts/execution-only.md)
- [Output Contract](./docs/contracts/output-structure.md)
- [Runtime Contract](./docs/contracts/runtime-state.md)
- [Non-Public / Internal Assets](./docs/internal/non-public-assets.md)
