# Run Blueprint

状态：Phase 1 已锁定  
用途：定义本项目 run 级目录、命名、资产落盘、引用锚点和最终播报规则。

## 1. 设计目标

- 让每次对话或任务都能以 run 为单位完整落盘
- 保证同一时间下的不同任务可以被区分
- 保证单链接数据、Prompt、分析报告和综合报告都能稳定定位
- 保证引用来源具备绝对路径和位置描述

## 2. run 目录规则

建议根目录：

- `runs/`

建议 run 命名：

- `run_<YYYYMMDD-HHMMSS>_<task-slug>`

示例：

- `run_20260403-143522_multi-link-ad-analysis`

说明：

- 时间戳用于保证时序可追踪
- `task-slug` 用于区分同一时刻附近的不同任务
- 若未来宿主天然提供 run id，可将其记录到 `run_manifest.json`

## 3. run 目录结构草案

```text
runs/
  run_20260403-143522_multi-link-ad-analysis/
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
      01_<完整标题>__<作者昵称>/
        manifests/
          note_manifest.json
          reference_index.json
        raw/
          note.json
          comments.json
          metrics.json
        images/
        assets/
          wordcloud.jpg
        analysis/
          <图文标题+作者名>_分析报告.md
    aggregate/
      <本次总结出的共有特点+时间戳>_综合分析报告.md
    logs/
      final_broadcast.md
```

## 4. 单链接目录命名

命名原则：

- 目录展示名遵循“完整标题 + 作者昵称”
- 为兼容文件系统，实际落盘时需要做安全化处理

建议格式：

- `<序号>_<sanitize(完整标题)>__<sanitize(作者昵称)>`

必须保留的原始值：

- 在 `note_manifest.json` 中保留原始 `title` 和 `author_nickname`

## 5. 文件命名规则

单篇报告：

- `<图文标题+作者名>_分析报告.md`

综合报告：

- `<本次总结出的共有特点+时间戳>_综合分析报告.md`

Prompt 文件：

- 标准 Prompt 被复制或引用到 `prompt/used_prompt.md`
- run 专属 Prompt 直接写入 `prompt/used_prompt.md`

输入记录：

- `raw_user_input.md`
- `invalid_links.md`

## 6. 引用锚点规则

所有关键结论都必须可回溯到本地文件。

引用标签：

- `[Tn]`：文本
- `[In]`：图片
- `[Cn]`：评论
- `[Dn]`：互动数据

每条引用至少包含：

- 类型
- 绝对路径
- 文件名
- 所属图文 ID 或链接标识
- 具体位置
- 必要时的摘录或说明

落盘位置：

- 每个链接目录中的 `manifests/reference_index.json`

## 7. Prompt 落盘规则

标准 Prompt：

- 来源于未来 skill 的 `assets/`
- 运行时引用到当前 run 的 `prompt/used_prompt.md`

run 专属 Prompt：

- 只能写入当前 run 的 `prompt/used_prompt.md`
- 不能进入 skill 全局 `assets/`
- 不能复用到其他 run

## 8. 非小红书链接处理

处理原则：

- 非 `http://xhslink.com/` 链接不纳入分析
- 仍需落盘到 `inputs/invalid_links.md`
- 在最终播报中明确列出

## 9. 最终播报模板

```md
✅ 小红书广告投放分析完成！

📁 输出目录: <当前 run 绝对路径>

📄 生成文件:
  - <图文标题+作者名>_分析报告.md
  - <本次总结出的共有特点+时间戳>_综合分析报告.md

⚠️ 未纳入分析的链接:
  - <非小红书链接 1>
  - <非小红书链接 2>

🔗 快速打开:
  [单篇分析报告](<单篇报告路径>)
  [综合分析报告](<综合报告路径>)
```

## 10. 验收条件

- run 命名、目录结构、单链接目录命名和报告命名无歧义
- Prompt 的全局资产与 run 局部资产边界无歧义
- 引用来源的最小字段集无歧义
- 实现者不需要再自行决定文件落盘位置
