# 依赖边界

这个技能只负责 Google Trends 关键词监控流程本身。

## 本技能负责

- Trends 健康检查逻辑
- `Related queries > Rising` 采集
- 与 `GPTs` 的 compare 页面判定
- 每次执行的 run 文档与 checkpoint 脚手架
- 通过 wrapper 编排 Feishu 读写
- 过滤、去重、重试、deferred 规则

## 本技能不负责

- Playwright MCP 安装
- 其他浏览器 MCP 安装
- 浏览器/CDP 环境初始化
- 代理软件安装或节点切换
- 飞书凭据创建
- Feishu 工具本身的实现

## 技能内置资源的解析规则

- 本技能里的 wrapper 脚本和参考文档都属于技能自带资源。
- `scripts/...` 和 `references/...` 路径默认都应从技能目录解析，不应先到当前仓库或工作区搜索副本。
- 工作区里没有同名脚本是正常情况，不算缺失依赖。
- 只有技能目录中缺少这些文件时，才说明技能打包不完整。

## 外部依赖缺失时的处理

当外部依赖缺失时，要立即停止并明确说明：

- 如果 `feishu-sheets-toolkit` 缺失或未配置：
  明确要求用户先安装或配置 `$feishu-sheets-toolkit`。
- 如果当前环境无法提供健康的浏览器/CDP 会话：
  明确要求用户先修复浏览器自动化环境。
  这个环境可以是本地浏览器 + CDP、Playwright MCP，或其他等价方案。

不要把其他技能的安装指南内联到这个技能里。
不要把其他技能的初始化逻辑复制到这个技能里。
