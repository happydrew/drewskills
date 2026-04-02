# AGENTS.md

Drew Grant Skills Hub 是一个公开的个人技能源仓库。

## 目标

本仓库的定位是：

- Drew Grant 维护的个人 skills source
- 遵循开放 agent skills 生态
- 让不同 agent 通过原生方式或开放安装器消费同一份技能源

## 权威入口

优先读取：

1. `hub.json`
2. `AGENTS.md`
3. `skills/`
4. `packs/`

## 目录说明

- `skills/`：唯一权威技能源
- `packs/`：技能逻辑分组
- `docs/`：使用与维护文档
- `scripts/`：校验与脚手架脚本

## 使用原则

- 优先使用 `npx skills`
- 补充使用 `npx openskills`
- Claude Code 与 Codex 优先沿用各自已有生态
- 不使用私有安装协议

## 约束

- 不要绕开 `skills/` 维护技能正文
- 不要提交任何本地安装结果目录
- 不要在技能文档、示例或脚本中写死本地绝对路径
- 不要臆造不存在的技能或版本
