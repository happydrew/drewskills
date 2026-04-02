---
name: import-third-party-skill
description: 当用户想把第三方开源技能或整仓技能集拉取、规范化并导入 Drew Grant 的个人 Skills Hub 时使用，支持在任意目录执行并自动处理临时工作目录。
---

# Import Third-Party Skill

你的任务是把第三方开源技能导入 Drew Grant 的个人 Skills Hub，并尽量把流程压缩成一次执行完成。

开始执行前先提醒用户：

- 优先提供“技能目录 URL”，不要只给仓库根 URL
- 如果给的是整个仓库 URL，最好额外说明它是单个 skill 还是多 skill 仓库
- 如果只导入一个 skill，最好同时给出该 skill 在仓库中的相对路径
- 技能执行时要在“当前目录”下创建一个专用临时工作目录，用于第三方下载、内部仓库克隆和中间文件处理

如果以下必要信息不完整，先停下来问用户，不要直接猜：

- 这个 URL 指向的是单个 skill，还是一个包含多个 skills 的仓库
- 用户要导入一个 skill，还是导入全部 skills
- 如果只导入一个 skill，该 skill 在仓库中的相对路径是什么
- 是否允许覆盖内部仓库中已有的同名技能
- 是否需要自动 commit / push

权威目标仓库：

- GitHub 仓库地址：`https://github.com/happydrew/drewskills`
- Git clone 地址：`https://github.com/happydrew/drewskills.git`
- 基础技能包：`foundation`

## 适用场景

- 用户明确提供了第三方技能仓库 URL、技能目录 URL，或本地技能目录路径
- 用户希望把外部技能快速搬运到 Drew Grant Skills Hub，而不是手工逐个复制文件
- 用户需要在任意目录执行导入，不希望依赖当前 shell 必须位于当前仓库根目录
- 用户希望导入时自动补齐 `skill.json`、`SKILL.md` frontmatter、pack 注册等基础规范
- 用户既可能要导入单个 skill，也可能要导入整仓库里的全部 skills

## 不适用场景

- 用户只是想安装第三方技能到本机 agent，而不是沉淀到内部仓库
- 用户给出的只是文章、文档片段或 issue 描述，并非可导入的技能目录或技能仓库
- 用户要求绕过 `skills/` 直接把文件塞到仓库其他目录
- 用户要求写入个人 token、私有路径或其他敏感信息

## 需要用户提供的信息

- 第三方技能来源，优先级如下：
  - 技能目录 URL，例如 `https://github.com/org/repo/tree/main/skills/foo`
  - 其他目录 URL，例如 `https://github.com/org/repo/tree/main/review`
  - 仓库 URL，例如 `https://github.com/org/repo.git`
  - 本地技能目录或本地技能仓库路径
- 来源类型：单个 skill，或多 skill 仓库
- 导入目标：只导入一个 skill，或导入全部 skills
- 如果只导入一个 skill，给出技能相对路径，例如 `skills/foo` 或 `review`
- 如需覆盖现有技能，明确说明允许替换
- 如需自动提交或推送，确认当前环境已具备对应 Git 权限

## 工作流

1. 先判断来源是否真的是 skill 或 skills 仓库
2. 在当前目录下创建单独的临时工作目录，统一放置：
   - 第三方仓库克隆目录
   - 内部 Skills Hub 临时克隆目录
   - 导入过程中的中间文件
3. 优先尝试在当前目录向上寻找 Skills Hub 仓库根目录；若找不到，再在临时工作目录中克隆目标仓库
4. 解析第三方来源：
   - 本地目录直接读取
   - 仓库 URL 先克隆，再扫描 skill
   - `.../tree/.../<dir>` 这类目录 URL 先拆出仓库、分支和目录子路径
5. 判断当前来源中究竟是：
   - 单个 skill
   - 一个含多个 skills 的仓库
   - 一个仓库中的某个子目录
   如果无法自动判断，明确提示缺少哪项信息，并停下来询问用户
6. 将技能复制到 `skills/<skill-name>/` 下，过滤 `.git`、安装产物和缓存目录
   - 单个导入时只处理一个技能
   - 批量导入时循环处理每个技能
7. 规范化导入结果：
   - 修正 `SKILL.md` frontmatter 的 `name` 与 `description`
   - 生成或覆盖 `skill.json`
   - 将技能加入 `packs/foundation-pack.json`
8. 若用户要求，执行 `git add`、`git commit`、`git push`
9. 仅当变更已安全落地时再删除临时工作目录；如果未 push，保留临时仓库路径给用户继续处理

## 执行入口

优先使用技能自带脚本：

```bash
python <skill-dir>/scripts/import_skill.py <source>
```

常用参数：

- `--source-kind skill|repo|auto`：指定来源是单个 skill 还是多 skill 仓库
- `--import-mode one|all|auto`：指定导入一个还是全部
- `--skill-path <path>`：指定单个 skill 的相对路径，或仓库中要扫描的子目录
- `--workspace-dir <path>`：指定临时工作目录的父目录；不传时默认在当前目录创建专用临时目录
- `--hub-dir <path>`：指定已存在的本地 hub 仓库目录
- `--dest-name <name>`：重命名单个导入后的技能目录
- `--replace`：允许覆盖已存在的技能目录
- `--commit`：导入后自动提交
- `--push`：导入后自动推送，隐含 `--commit`
- `--keep-temp`：即使推送成功也保留临时目录

## 输出要求

- 直接给出导入是否成功
- 如果因为信息不完整而无法确定导入方案，要明确列出缺失信息并要求补充
- 明确写出目标仓库路径、目标技能目录和是否更新了 `foundation` 包
- 如果使用了临时工作目录，说明工作目录是否已删除
- 如果未推送成功，必须给出后续可执行命令或残留工作目录

## 禁止事项

- 不要臆造不存在的第三方技能目录或仓库结构
- 不要把技能安装目录、缓存目录或 `.git` 元数据一并提交进 `skills/`
- 不要绕开 `skills/` 直接写技能文件
- 不要在技能文件中写入个人 token、私有地址或本地专属绝对路径
