from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HUB_CONFIG = ROOT / "hub.json"
SKILLS_DIR = ROOT / "skills"
PACKS_DIR = ROOT / "packs"
FORBIDDEN_INSTALL_DIRS = [".agent", ".agents", ".claude"]


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if len(lines) < 3 or lines[0].strip() != "---":
        raise ValueError(f"{path} must start with YAML frontmatter")

    end_index = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end_index = idx
            break

    if end_index is None:
        raise ValueError(f"{path} frontmatter is not terminated")

    frontmatter: dict[str, str] = {}
    for line in lines[1:end_index]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        frontmatter[key.strip()] = value.strip()
    return frontmatter


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_no_install_artifacts() -> None:
    found = [name for name in FORBIDDEN_INSTALL_DIRS if (ROOT / name).exists()]
    ensure(
        not found,
        "Repository must not contain installed skill directories: "
        + ", ".join(found)
        + ". Remove local install outputs before committing.",
    )


def validate_hub_config() -> None:
    ensure(HUB_CONFIG.exists(), f"Missing hub config: {HUB_CONFIG}")
    config = load_json(HUB_CONFIG)
    ensure("owner" in config, f"{HUB_CONFIG} missing 'owner'")
    ensure("repository" in config, f"{HUB_CONFIG} missing 'repository'")
    ensure(bool(config["owner"].get("name")), f"{HUB_CONFIG} owner.name cannot be empty")
    ensure(bool(config["owner"].get("code")), f"{HUB_CONFIG} owner.code cannot be empty")
    ensure(bool(config["repository"].get("provider")), f"{HUB_CONFIG} repository.provider cannot be empty")
    ensure(bool(config["repository"].get("cloneUrl")), f"{HUB_CONFIG} repository.cloneUrl cannot be empty")
    ensure(bool(config["repository"].get("webUrl")), f"{HUB_CONFIG} repository.webUrl cannot be empty")


def validate_skills_dir(skills_dir: Path) -> list[str]:
    ensure(skills_dir.exists(), f"Missing skills directory: {skills_dir}")
    skill_names: list[str] = []

    for skill_dir in sorted(path for path in skills_dir.iterdir() if path.is_dir()):
        skill_manifest = skill_dir / "skill.json"
        skill_doc = skill_dir / "SKILL.md"
        ensure(skill_manifest.exists(), f"Missing skill manifest: {skill_manifest}")
        ensure(skill_doc.exists(), f"Missing skill document: {skill_doc}")

        skill = load_json(skill_manifest)
        frontmatter = parse_frontmatter(skill_doc)

        folder_name = skill_dir.name
        ensure(skill.get("name") == folder_name, f"{skill_manifest} name must equal folder name '{folder_name}'")
        ensure(frontmatter.get("name") == folder_name, f"{skill_doc} frontmatter name must equal folder name '{folder_name}'")
        ensure("description" in frontmatter and frontmatter["description"], f"{skill_doc} missing frontmatter description")

        for field in ("title", "description", "owners", "tags", "agents", "pack", "status"):
            ensure(field in skill, f"{skill_manifest} missing '{field}'")

        ensure(bool(skill["owners"]), f"{skill_manifest} owners cannot be empty")
        ensure(bool(skill["agents"]), f"{skill_manifest} agents cannot be empty")
        ensure(skill["status"] in {"draft", "stable", "deprecated"}, f"{skill_manifest} status must be draft/stable/deprecated")
        skill_names.append(folder_name)

    return skill_names


def validate_pack(pack_path: Path, skill_names: list[str]) -> None:
    pack = load_json(pack_path)
    for field in ("name", "version", "plugin", "skills"):
        ensure(field in pack, f"{pack_path} missing '{field}'")

    valid_skills = set(skill_names)
    for skill_name in pack["skills"]:
        ensure(skill_name in valid_skills, f"{pack_path} references unknown skill '{skill_name}'")

    version = pack["version"]
    ensure(bool(re.fullmatch(r"\d+\.\d+\.\d+", version)), f"{pack_path} version must use semver 'X.Y.Z'")


def main() -> int:
    if not SKILLS_DIR.exists():
        print(f"Missing skills directory: {SKILLS_DIR}", file=sys.stderr)
        return 1

    skill_count = 0

    try:
        validate_no_install_artifacts()
        validate_hub_config()
        skill_names = validate_skills_dir(SKILLS_DIR)
        skill_count = len(skill_names)

        for pack_path in sorted(PACKS_DIR.glob("*.json")):
            validate_pack(pack_path, skill_names)
    except ValueError as exc:
        print(f"Validation failed: {exc}", file=sys.stderr)
        return 1

    print(f"Validated {skill_count} skill(s) and {len(list(PACKS_DIR.glob('*.json')))} pack(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
