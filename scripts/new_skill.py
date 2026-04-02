from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"


def parse_resources(raw: str) -> list[str]:
    if not raw.strip():
        return []
    resources = [item.strip() for item in raw.split(",") if item.strip()]
    valid = {"scripts", "references", "assets", "templates", "examples"}
    invalid = [item for item in resources if item not in valid]
    if invalid:
        raise ValueError(f"Unsupported resources: {', '.join(invalid)}")
    return resources


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a new skill scaffold for Drew Grant Skills Hub.")
    parser.add_argument("--name", required=True, help="Skill directory name, use kebab-case")
    parser.add_argument("--title", required=True, help="Human-readable skill title")
    parser.add_argument("--description", required=True, help="Short description")
    parser.add_argument("--owner", default="happydrew", help="Owner id")
    parser.add_argument("--pack", default="foundation", help="Pack name")
    parser.add_argument("--agents", nargs="+", default=["claude-code", "codex"], help="Supported agents")
    parser.add_argument("--tags", nargs="*", default=[], help="Optional tags")
    parser.add_argument(
        "--resources",
        default="",
        help="Optional resource directories, comma-separated: scripts,references,assets,templates,examples",
    )
    args = parser.parse_args()
    resources = parse_resources(args.resources)

    skill_dir = SKILLS_DIR / args.name
    skill_dir.mkdir(parents=True, exist_ok=False)

    frontmatter = (
        f"---\n"
        f"name: {args.name}\n"
        f"description: {args.description}\n"
        f"---\n\n"
        f"# {args.title}\n\n"
        "## 适用场景\n\n"
        "- 在这里写清楚这个技能解决什么问题\n"
        "- 说明哪些用户请求会触发这个技能\n\n"
        "## 不适用场景\n\n"
        "- 在这里写清楚什么情况不应该使用这个技能\n\n"
        "## 需要用户提供的信息\n\n"
        "- 在这里列出执行这个技能前需要的输入材料\n\n"
        "## 工作流程\n\n"
        "1. 先确认问题范围\n"
        "2. 再收集必要输入\n"
        "3. 按步骤执行核心工作流\n"
        "4. 给出明确结果和下一步建议\n\n"
        "## 输出要求\n\n"
        "- 结论要直接\n"
        "- 命令要可复制执行\n"
        "- 文件路径、分支名、MR 信息等要写准确\n\n"
        "## 禁止事项\n\n"
        "- 不要臆造不存在的事实\n"
        "- 不要输出敏感信息\n"
    )
    (skill_dir / "SKILL.md").write_text(frontmatter, encoding="utf-8")

    manifest = {
        "name": args.name,
        "title": args.title,
        "description": args.description,
        "owners": [args.owner],
        "tags": args.tags,
        "agents": args.agents,
        "pack": args.pack,
        "status": "draft",
    }
    (skill_dir / "skill.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for resource in resources:
        (skill_dir / resource).mkdir(parents=True, exist_ok=True)

    print(f"Created skill scaffold at {skill_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
