# Contributing

本仓库维护 Drew Grant 的公开技能源。

## 基本规则

- 唯一权威技能源：`skills/`
- 所有技能正文只在 `skills/` 中维护
- 不提交任何本地安装结果目录
- 不引入私有安装协议
- 技能内容和示例必须能在任意环境下使用，不能依赖作者本机路径

## 新增技能

推荐使用脚手架：

```powershell
python .\scripts\new_skill.py `
  --name my-new-skill `
  --title "My New Skill" `
  --description "One-line description for the skill"
```

## 提交前必须执行

```powershell
python .\scripts\validate_registry.py
```

## 评审标准

- 技能触发场景明确
- 不适用场景明确
- 单一职责
- 无敏感信息
- owner 明确
- 适用 agent 明确
- 文档、命令和示例不包含本地绝对路径
