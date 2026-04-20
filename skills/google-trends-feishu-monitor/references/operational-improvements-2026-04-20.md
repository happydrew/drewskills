# 2026-04-20 运行复盘与优化

这份文档用于沉淀 `2026-04-20` 实跑暴露出的真实问题、对应解决方法，以及技能层面已经落地或建议落地的优化。

## 1. 本轮主要阻塞点

### 1.1 CDP 会话缺失会直接阻塞任务启动

现象：

- `health` 首次执行时报 `connect ECONNREFUSED 127.0.0.1:9225`

原因：

- `trends_cdp_collect.mjs` 默认要求本地已有一个健康的 Chromium/Edge CDP 会话
- 技能以前只把这件事当作外部前提，没有把“如何快速识别缺的是会话而不是代理”说清楚

处理：

- 先确认本地 `9225` 是否监听
- 若未监听，再启动本地 Edge CDP 会话并重试 `health`

优化：

- 文档中明确把 `127.0.0.1:9225` 写成默认口径，减少误判
- 仍然保持边界：技能不负责安装浏览器，但允许操作者先手动补起本地 CDP 会话

### 1.2 手工拼装批处理脚本容易在 JSON/编码层绕远路

现象：

- PowerShell 下 `ConvertFrom-Json -Depth` 兼容性不一致
- 候选词去重阶段曾把 148 个词误拼成一个长字符串
- compare 子进程异常时，曾生成 `result: null` 的空结果文件

原因：

- 之前技能只有基础脚本，没有正式的 end-to-end orchestrator
- 运行时只能现场拼接 PowerShell 批处理，容错和结构校验都不够

处理：

- 本轮新增 `scripts/run_monitor_batch.py`
- 把 `health -> read -> related -> dedupe -> compare -> write -> verify` 固化成一个脚本

优化：

- 以后优先用 Python orchestrator，不再依赖临时 PowerShell 管道拼 JSON
- compare 结果全部逐项落盘，便于断点恢复和复核

### 1.3 Feishu 写回的 payload 形状和编码需要强约束

现象：

- 第一次写回报 `valueRange is wrong`
- 后来确认是 payload 不是二维数组
- 另一次写入时中文列被写成 `??`

原因：

- 手工 PowerShell 序列化把数组写成了对象数组
- 中间链路用错了文本来源，导致中文先被污染再写进飞书

处理：

- 统一要求写回文件必须是标准二维数组 JSON
- 写回 payload 必须由 Python/Node 直接生成 UTF-8 文件，避免 PowerShell 文本拼装
- 写完后必须回读同一区域并核对 revision / values

优化：

- `run_monitor_batch.py` 直接生成二维数组 JSON 并做写后校验

### 1.4 Feishu wrapper 对错误返回和写入回执不够清晰

现象：

- 某些失败情况下，wrapper 不会直接把业务错误抛成清晰失败
- 写成功时，历史版本的 toolkit 也可能没有完整返回 `updatedRange` / `revision`

处理：

- 本轮同时修正了 `feishu-sheets-toolkit` 的写回结果解包逻辑

优化：

- 以后 Google Trends 技能仍通过 wrapper 调用飞书
- 但判断成功与否时，必须以“写后 readback + revision 变化”为最终标准，不能只信命令退出码

## 2. 流程层面的缺陷

### 2.1 Related 阶段和 Compare 阶段缺少正式收口脚本

缺陷：

- 之前技能只给了单步命令，没有给“批量执行”的标准实现

后果：

- 容易出现临时脚本口径漂移
- 同样的问题会重复踩

改进：

- 新增 `scripts/run_monitor_batch.py`

### 2.2 运行规则里没有沉淀最近一次的真实经验

缺陷：

- 文档里没把 `CDP 9225`、`二维数组 payload`、`UTF-8 写回` 这些具体坑写清楚

改进：

- 新增本复盘文档
- 更新 `runtime-prereqs.md`
- 更新 `SKILL.md`

### 2.3 暴涨词阈值需要抬高

旧规则：

- `> 2000%` 或 `Breakout`

新规则：

- `> 3000%` 或 `Breakout`

原因：

- 2000% 阈值下噪音仍偏多
- 本轮大量候选最终在 compare 阶段被淘汰，前置阈值提高后更利于收缩 compare 成本

## 3. 已落地优化

- 新增 `scripts/run_monitor_batch.py`
- 将暴涨词阈值改为 `> 3000%` 或 `Breakout`
- 文档中补充了 `9225` CDP 前提说明
- 文档中补充了写回 payload 必须是 UTF-8 二维数组 JSON 的要求
- 文档中补充了“写入结果必须通过 readback 确认”的要求

## 4. 后续仍建议继续优化的点

- 如果 compare 成本继续偏高，可在 compare 前增加更强预过滤
- 如果需要更稳的断点恢复，可把 compare 结果合并出一个明确的 state file
- 如果后续确认本地长期都用 Edge + CDP，可再单独做一个浏览器会话辅助技能，但不要混进本技能
