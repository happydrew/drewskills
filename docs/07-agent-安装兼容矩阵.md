# Agent 安装兼容矩阵

## 1. 安装原则

- Claude Code、Codex 使用 `npx skills`
- 通用 agent 使用 `npx openskills`
- 同一个 agent 只安装一次

## 2. 安装整个仓库

| Agent | 安装命令 | 说明 |
| --- | --- | --- |
| Claude Code | `npx skills add https://github.com/happydrew/drewskills.git --agent claude-code -g --yes` | 全局安装整个 source |
| Codex | `npx skills add https://github.com/happydrew/drewskills.git --agent codex -g --yes` | 全局安装整个 source |
| Universal | `npx openskills install https://github.com/happydrew/drewskills.git --universal -y` | 安装整个 source |

## 3. 安装指定技能

| Agent | 安装命令 | 说明 |
| --- | --- | --- |
| Claude Code / Codex | `npx skills add https://github.com/happydrew/drewskills.git --agent codex -g --skill import-third-party-skill --yes` | 直接按技能名安装 |
| Universal | `npx openskills install ./drewskills/skills/import-third-party-skill --universal -y` | 先获取仓库内容，再安装技能目录 |

## 4. 当前技能

- `git-commit-and-push`
- `import-third-party-skill`
