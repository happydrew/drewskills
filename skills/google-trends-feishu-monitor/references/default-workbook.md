# 默认工作簿

这个技能当前默认使用的工作簿：

- 工作簿 URL：`https://b8vf2u0bp3.feishu.cn/sheets/SG4xs1FjdhernxtTw9ucwBUAnGb`
- 输出表：`每日找词` / `rBLswo`

输入表：

- 工具词根表：`常用工具词根+trends链接` / `oUaATj`
- 只处理第 `2-12` 行
- 忽略第 `13-19` 行

- 游戏词根表：`大游戏站名称+trends链接` / `2gLvk3`
- 只处理存在有效 `trends url` 的行
- 当前已知有效范围：第 `2-6` 行

`每日找词` 的输出列：

- `A` 词根
- `B` 暴涨词
- `C` trends截图
- `D` 关键词意图研究
- `E` 日期
- `F` 词根类型（工具、游戏）

字段规则：

- `trends截图` 存储 Google Trends compare 分析链接，不存图片
- `关键词意图研究` 使用简短中文摘要
- 按 `日期 + 暴涨词` 去重
