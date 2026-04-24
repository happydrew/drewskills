# 运行前置条件

只有在环境满足下面全部条件时，才使用这个技能：

- Windows 机器，且可使用 PowerShell
- `PATH` 中可用 `Node.js`
- 本机已安装 Microsoft Edge 或 Google Chrome 之一
- 默认 Trends 采集脚本会连接 `127.0.0.1:9225`
- 面向 Google Trends 的稳定代理出口，最好是美国住宅代理
- `$CODEX_HOME/skills` 下已经安装 `feishu-sheets-toolkit`
- `feishu-sheets-toolkit` 已完成飞书凭据初始化

这个技能不负责安装浏览器、配置代理或处理系统级浏览器环境。
如果本地 `9225` 没监听，wrapper 会先尝试补起本地 Edge/Chrome CDP 会话；如果自动补起后仍然无法提供健康的浏览器/CDP 环境，再停止并要求用户修复对应环境。

推荐的验证顺序：

1. 先确认本机已安装 Edge/Chrome，且代理出口已准备好
2. 如果当前已经有稳定的本地 `127.0.0.1:9225` CDP 会话，优先复用，不要频繁更换临时 profile
3. 如果本地 `9225` 没监听，先让 `scripts/run_trends_collect.ps1` 自动尝试补起本地 Edge/Chromium CDP 会话
4. 如果脚本仍报 `ECONNREFUSED 127.0.0.1:9225`，优先判断为“本地 CDP 会话补起失败”，不要先误判为代理问题
5. 运行 `powershell -ExecutionPolicy Bypass -File scripts/run_trends_collect.ps1 health "<one trends url>"`
6. 确认 Google 首页可达
7. 确认 Trends explore 页面能打开
8. 确认所有 `relatedStatuses` 都是 `200`

如果 `relatedsearches` 返回 `429`，不要继续批量执行。应先等待并重试，必要时更换代理或出口 IP。
