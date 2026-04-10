# 小红书广告投放策略分析工具

[English](#english) | 中文文档

<div align="center">

**🤖 Agent Skill** | AI 驱动的小红书多模态投放分析工具

[![Tested on: Gemini 3.1 Pro & ChatGPT 5.4](https://img.shields.io/badge/测试环境-Gemini_3.1_Pro_|_ChatGPT_5.4-blue)](https://gemini.google.com)
[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-green.svg)](https://creativecommons.org/licenses/by-nc/4.0/)

</div>

> ### **🎯 一站式小红书（Rednote）爆款图文提取与广告投放策略分析工具。支持多链接异步抓取，对图片、正文、评论及交互数据进行多模态深度耦合分析，精准提炼爆款共性，赋能品牌高效制定投放决策。**

## 💡 核心场景与产品价值

**解决的痛点：**
- **人工拆解耗时费力**：分析一篇竞品或爆款笔记需要反复查看图文、翻阅评论区，耗费大量时间。
- **分析维度单一割裂**：传统工具往往只看文本或只看数据，忽略了“图片视觉+文案情绪+评论区真实反馈”的**多模态深度耦合**效应。
- **缺乏可复制的方法论**：难以从多篇爆款中快速抽象出底层的“广告投放共性”与“高转化逻辑”。

**带来的好处（核心价值）：**
- ⚡ **极致提效**：只需输入链接，喝杯咖啡的时间（7-10分钟/3篇笔记），即可获取深度洞察报告。
- 🧠 **全景透视**：不仅仅是总结，而是从“受众心理-视觉抓手-评论互动”全链路透视笔记的真实种草价值。
- 💰 **赋能决策**：直接产出具指导意义的广告投放策略，降低试错成本，提高 ROI（投资回报率）。

## ✨ 功能特性

| 阶段 | 功能 | 说明 |
|------|------|------|
| 1️⃣ | **异步多任务抓取** | 支持同时输入多条笔记链接，多任务并发执行 |
| 2️⃣ | **多模态数据提取** | 全方位抓取：高清图片 / 正文文本 / 评论区对话 / 赞藏评交互数据 |
| 3️⃣ | **深度耦合分析** | 图文匹配度检测 + 评论区情感计算 + 核心受众画像逆向推导 |
| 4️⃣ | **共性价值提炼** | 跨笔记横向对比，提炼“视觉/文案/互动”维度的爆款共性模板 |

## 🚀 快速开始

### 环境要求

本项目作为高阶 Agent Skill，底层采用了现代化的异步架构与多模态解析栈（推荐 Python 3.8+）。

```bash
# 推荐通过依赖清单一键安装
pip install -r requirements-execution.txt
```

**核心依赖组件与引擎解析：**

* **🌐 异步爬取与自动化引擎**：
  * `playwright`：强大的无头浏览器驱动，从容应对小红书复杂的动态渲染与反爬机制。
  * `httpx` & `aiofiles`：提供原生的高性能异步 HTTP 请求与底层异步文件 IO，保障多任务抓取效率。
* **🧠 多模态视觉计算栈**：
  * `opencv-python` & `Pillow`：负责处理高清图文素材，提取视觉抓手特征（Visual Hooks）。
* **💬 文本与情绪分析引擎**：
  * `jieba` & `wordcloud`：精准解构评论区中文高频词与情绪槽点，支持受众深潜诊断。
* **📊 数据运算与工程健壮性**：
  * `redis`：高并发多任务队列的性能保障，支持大规模并发抓取的任务调度与缓存。
  * `pydantic` & `pyhumps`：严格校验并格式化多模态解析返回的复杂 JSON 数据模型。
  * `numpy` & `matplotlib`：数据矩阵计算与投放转化率的底层图表支持。
  * `tenacity`：赋予网络请求极强的智能重试与容错容灾能力。

### 安装指南

这是一个 **Agent Skill**，专为高度自治的 AI 代理设计。将其安装到你的 Agent 工作区（如 `.agent/skills/` 目录）：

```bash
git clone https://github.com/Sober-Zang/rednote-ads-placement-analysis.git .agent/skills/rednote-ads-placement-analysis
```

### 使用方法

在支持的 IDE 或对话窗口中，本工具的交互逻辑极为简捷：

* **👉 极简触发（默认模式）**：只需直接粘贴小红书链接，Agent 就会自动识别、下载素材，并执行标准的广告投放深度分析。
* **🧠 意图覆盖（自定义模式）**：如果在提供链接的同时，你输入了额外的提示词（例如：“重点帮我分析这几篇笔记中关于‘价格’的评论区情绪”），Agent 依然会自动完成下载，但会严格按照你的新指令出具针对性报告。
* **🔇 边界隔离**：如果你发送的内容中不包含任何小红书链接，该 Skill 将保持完全静默，绝不干扰你与 Agent 的其他常规对话。

**交互示例：** 直接输入以下内容：
> [https://xhslink.com/xxxx1](https://xhslink.com/xxxx1)
> [https://xhslink.com/xxxx2](https://xhslink.com/xxxx2)
> [https://xhslink.com/xxxx3](https://xhslink.com/xxxx3)

Agent 将自动分析这 3 篇小红书笔记的广告投放共性价值，并提取可复用的爆款逻辑。

*⏱️ **注**：得益于多任务异步执行机制，处理 3 条复杂图文笔记平均仅需 **7-10 分钟**（首次运行可能因环境配置耗时较长，属正常现象，请耐心等待）。*

## 🎯 多模态深度耦合解析流

传统分析工具通常采取线性处理，而本 Skill 采用**深度耦合架构**，还原最真实的用户浏览与种草链路：

```
小红书笔记链接池 (多任务输入)
    ↓
[并行抓取层] ──→ 图片流 ──→ 文本流 ──→ 评论流 ──→ 交互指标
    ↓ 
[跨模态融合计算层] 
  ├── 👁️ 视觉-文本耦合：图片信息量与文案 Hook 是否匹配？
  ├── 💬 文本-评论耦合：正文埋点是否成功引导评论区互动（课代表/槽点）？
  └── 📊 情绪-指标耦合：评论区正负向情感与最终点赞/收藏比率的关系？
    ↓
输出 高价值投放策略报告
```

## 📊 三维度投放分析框架

### 1. Visual-Textual Resonance（图文共振分析）
- 头图视觉抓手拆解（构图/色彩/文字排版）
- 标题/正文 Hook 诱因与流量密码识别
- 模态一致性评估（图文是否相符，是否形成信息互补）

### 2. Audience-Interaction Deep Dive（受众互动深潜）
- 核心受众画像逆向推导
- 评论区高频词与情感倾向（Sentiment Analysis）计算
- 社交货币与传播节点（槽点、共鸣点、干货点）诊断

### 3. Ads-Placement Actionable Logic（投放实操逻辑提炼）
- 横向共性分析（多篇笔记的底层爆款公式）
- 品牌/产品自然植入位点建议
- 转化漏斗优化（从浏览到行动的 CTA 建议）

## 📁 项目结构

```bash
rednote-ads-placement-analysis/
├── docs/                                  # 执行契约与内部说明文档
│   ├── contracts/
│   │   ├── execution-only.md              # 执行边界约束
│   │   ├── output-structure.md            # 输出目录与产物结构约定
│   │   └── runtime-state.md               # 运行期状态约定
│   └── internal/
│       └── non-public-assets.md           # 非公开资产说明
├── rednote-ads-placement-analyzer/        # 核心产品目录
│   ├── assets/
│   │   └── standard_analysis_prompt.md    # 标准分析提示资产
│   ├── evals/
│   │   ├── fixtures/                      # 评测样例
│   │   └── evals.json                     # 评测配置
│   ├── references/
│   │   └── xhs-platform-context.md        # 小红书平台背景参考
│   ├── scripts/
│   │   ├── _common.py                     # 公共工具与共享逻辑
│   │   ├── check_environment.py           # 环境检查脚本
│   │   ├── run_pipeline.py                # 主执行流水线脚本
│   │   └── validate_contract.py           # 契约校验脚本
│   ├── vendor/
│   │   └── mediacrawler_xhs/              # 引入的抓取能力代码
│   └── SKILL.md                           # 产品技能与执行说明
├── .gitignore
├── README.machine.md                      # 面向机器执行的仓库说明
├── pipeline.py                            # 官方命令入口
└── requirements-execution.txt             # 执行依赖
```

## 📄 输出文件

分析任务完成后，你的 Agent 会自动生成并整理以下产出物料：

```text
📁 输出目录 (Output_Directory)
│
├── 📂 1_核心决策产出 (Core_Reports)  <-- 【最重要：直接面向用户的价值产物】
│   ├── 📄 {任务主题}_综合分析报告.md        # 原 aggregate 真实感与阵地化运作...综合分析报告.md
│   └── 📄 {笔记标题}_单篇分析报告.md        # 原 notes 167cm94斤...单篇分析报告.md (多篇对应多个文件)
│
├── 📂 2_多模态素材库 (Multimodal_Assets) <-- 【次重要：沉淀的原始数据与中间层分析】
│   ├── 📂 图像与视觉素材 (Images)/
│   │   └── 🖼️ {序号}.jpg                   # 原 0.jpg, 1.jpg, 2.jpg... (提取的无水印原图)
│   │
│   ├── 📂 评论生态数据 (Comments)/
│   │   ├── 📄 comments.md / .json          # 抓取的全量评论文本与结构化数据
│   │   ├── 📊 comments_word_freq.json      # 评论区高频词统计
│   │   └── 🖼️ comments_word_cloud.png      # 评论情绪词云图
│   │
│   └── 📂 正文与互动指标 (Metadata)/
│       ├── 📄 note_text.md / note.json     # 笔记正文及结构化内容
│       └── 📄 meta.json / metrics.json     # 赞藏评转化率及基础元数据
│
└── 📂 3_系统运行组件 (System_Components) <-- 【最次要：用于追溯、调试和程序流转】
    ├── 📂 配置文件 (Configs)/
    │   ├── ⚙️ inputs / prompt              # 原始输入链接与下发的提示词配置
    │   └── ⚙️ manifests                    # 任务清单与执行配置
    │
    └── 📂 运行日志 (Logs)/
        ├── 📝 logs/                        # 基础运行与报错日志
        └── 📝 final_broadcast.md           # 原 logs final_broadcast.md (执行完毕的系统广播/通告)
```
        
*(注：原聚合用的 `aggregate`, `creators`, `notes` 文件夹已按其功能属性被整合进上述逻辑分类中)*

## 🎯 支持环境

本项目对现代主流的大语言模型及开发平台进行了深度适配与验证。**实测证明，具有多模态理解能力的前沿模型能发挥本 Skill 的最大威力：**

| 环境/平台 | 推荐模型引擎 | 状态 | 表现评价 |
|------|------|------|------|
| **Google Antigravity** | Gemini 3.1 Pro | ✅ **强力推荐** | 原生多模态解析能力极强，图文耦合分析极其精准 |
| **Codex** | ChatGPT 5.4 | ✅ **已充分测试** | 逻辑推理缜密，共性提炼与商业报告撰写极其优秀 |
| **Cursor** | 适配模型 | ✅ 支持 | 代码执行与文件IO极度稳定 |
| **Windsurf / Trae** | Claude / GPT系 | ✅ 支持 | 能够顺滑完成异步调度任务 |

## 📝 许可证

本项目采用 Creative Commons Attribution-NonCommercial 4.0 International License（CC BY-NC 4.0）许可。
你可以在非商业前提下自由使用、修改和二次创作本项目；任何商业用途需另行获得授权。

---