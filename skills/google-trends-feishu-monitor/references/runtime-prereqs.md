# 运行前置条件

只有在环境满足下面全部条件时，才使用这个技能：

- Windows 机器，且可使用 PowerShell
- `PATH` 中可用 `Node.js`
- 已经存在可用且健康的浏览器/CDP 环境
- 默认 Trends 采集脚本会连接 `127.0.0.1:9225`
- 面向 Google Trends 的稳定代理出口，最好是美国住宅代理
- `$CODEX_HOME/skills` 下已经安装 `feishu-sheets-toolkit`
- `feishu-sheets-toolkit` 已完成飞书凭据初始化

这个技能不负责安装或配置浏览器环境。
如果浏览器/CDP 或 MCP 浏览器自动化环境还没准备好，就应立即停止，并要求用户先完成对应环境配置。

推荐的验证顺序：

1. 先确认当前已经存在 CDP 浏览器会话，或其他等价的浏览器自动化环境
2. 如果脚本报 `ECONNREFUSED 127.0.0.1:9225`，优先判断为“本地 CDP 会话缺失”，不要先误判为代理问题
3. 推荐复用稳定的本地 Edge/Chromium CDP 会话，而不是在任务中频繁创建临时 profile
4. 运行 `powershell -ExecutionPolicy Bypass -File scripts/run_trends_collect.ps1 health "<one trends url>"`
5. 确认 Google 首页可达
6. 确认 Trends explore 页面能打开
7. 确认所有 `relatedStatuses` 都是 `200`

如果 `relatedsearches` 返回 `429`，不要继续批量执行。应先等待并重试，必要时更换代理或出口 IP。
