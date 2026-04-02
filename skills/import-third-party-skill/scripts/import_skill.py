from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


HUB_REPO_URL = "https://github.com/happydrew/drewskills.git"
DEFAULT_PACK = "foundation"
DEFAULT_OWNERS = ["happydrew"]
DEFAULT_AGENTS = ["claude-code", "codex"]
DEFAULT_TAGS = ["third-party", "imported", "migration"]
FORBIDDEN_COPY_NAMES = {
    ".git",
    ".github",
    ".gitlab",
    ".agent",
    ".agents",
    ".claude",
    "__pycache__",
    "node_modules",
}
FORBIDDEN_COPY_SUFFIXES = {".pyc", ".pyo", ".DS_Store"}


class ImportErrorWithHint(RuntimeError):
    pass


def run_git(args: list[str], cwd: Path | None = None) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd else None,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def sanitize_name(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    normalized = re.sub(r"-{2,}", "-", normalized)
    if not normalized:
        raise ImportErrorWithHint("Unable to infer a valid skill name from the source. Use --dest-name.")
    return normalized


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    lines = text.splitlines()
    if len(lines) < 3 or lines[0].strip() != "---":
        return {}, text

    end_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end_index = index
            break

    if end_index is None:
        return {}, text

    frontmatter: dict[str, str] = {}
    for line in lines[1:end_index]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        frontmatter[key.strip()] = value.strip()

    body = "\n".join(lines[end_index + 1 :]).lstrip("\n")
    return frontmatter, body


def render_frontmatter(frontmatter: dict[str, str], body: str) -> str:
    lines = ["---"]
    for key in ("name", "description"):
        lines.append(f"{key}: {frontmatter.get(key, '').strip()}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines) + body.rstrip() + "\n"


def read_markdown_title(body: str) -> str | None:
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return None


def summarize_description(body: str) -> str:
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("- ") or stripped.startswith("```"):
            continue
        return re.sub(r"\s+", " ", stripped)[:120]
    return "Imported third-party skill for Drew Grant Skills Hub."


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def find_hub_root(start: Path) -> Path | None:
    for candidate in [start, *start.parents]:
        if (candidate / "hub.json").exists() and (candidate / "skills").exists() and (candidate / "packs").exists():
            return candidate
    return None


def clone_repo(repo_url: str, target_dir: Path, ref: str | None = None) -> None:
    args = ["clone", repo_url, str(target_dir)]
    if ref:
        args = ["clone", "--branch", ref, "--single-branch", repo_url, str(target_dir)]
    run_git(args)


def parse_tree_url(source: str) -> tuple[str, str, str] | None:
    parsed = urlparse(source)
    if parsed.scheme not in {"http", "https"}:
        return None

    path = parsed.path.rstrip("/")
    marker = next((item for item in ("/-/tree/", "/tree/") if item in path), None)
    if not marker:
        return None

    repo_path, trailing = path.split(marker, 1)
    if "/" not in trailing:
        return None
    ref, directory_suffix = trailing.split("/", 1)
    repo_url = f"{parsed.scheme}://{parsed.netloc}{repo_path}.git"
    return repo_url, ref, directory_suffix


def create_workspace_dir(base_dir: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    workspace_dir = base_dir / f".tmp-import-third-party-skill-{timestamp}"
    suffix = 0
    while workspace_dir.exists():
        suffix += 1
        workspace_dir = base_dir / f".tmp-import-third-party-skill-{timestamp}-{suffix}"
    workspace_dir.mkdir(parents=True, exist_ok=False)
    return workspace_dir


def looks_like_repo_url(source: str) -> bool:
    parsed = urlparse(source)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc and parsed.path)


def is_skill_dir(path: Path) -> bool:
    return path.is_dir() and (path / "SKILL.md").exists()


def scan_for_skills(root: Path) -> list[Path]:
    candidates: list[Path] = []

    if is_skill_dir(root):
        return [root]

    direct_skills_dir = root / "skills"
    if direct_skills_dir.exists():
        for path in sorted(direct_skills_dir.iterdir()):
            if is_skill_dir(path):
                candidates.append(path)
        if candidates:
            return candidates

    for path in sorted(root.iterdir()):
        if is_skill_dir(path):
            candidates.append(path)
    return candidates


def resolve_local_target(base_dir: Path, relative_path: str | None) -> Path:
    if relative_path:
        candidate = (base_dir / relative_path).resolve()
        if not candidate.exists():
            raise ImportErrorWithHint(f"Specified path not found in source: {relative_path}")
        return candidate
    return base_dir


def resolve_source_root(source: str, temp_root: Path) -> tuple[Path, str]:
    local_path = Path(source).expanduser()
    if local_path.exists():
        resolved = local_path.resolve()
        if resolved.is_file():
            raise ImportErrorWithHint(f"Source must be a directory, got file: {resolved}")
        return resolved, str(resolved)

    tree_url = parse_tree_url(source)
    if tree_url:
        repo_url, ref, directory_suffix = tree_url
        checkout_dir = temp_root / "source-repo"
        clone_repo(repo_url, checkout_dir, ref=ref)
        root = resolve_local_target(checkout_dir, directory_suffix)
        return root, f"{repo_url}@{ref}:{directory_suffix}"

    if looks_like_repo_url(source):
        checkout_dir = temp_root / "source-repo"
        clone_repo(source, checkout_dir)
        return checkout_dir, source

    raise ImportErrorWithHint(
        "Unsupported source. Provide a local directory, a repository URL, or a direct directory URL."
    )


def choose_skill_paths(
    source_root: Path,
    source_label: str,
    source_kind: str,
    import_mode: str,
    skill_path: str | None,
) -> list[Path]:
    explicit_root = resolve_local_target(source_root, skill_path)

    if source_kind == "skill":
        if not is_skill_dir(explicit_root):
            raise ImportErrorWithHint(
                f"Source was declared as a single skill, but SKILL.md was not found: {explicit_root}"
            )
        return [explicit_root]

    if source_kind == "repo":
        skills = scan_for_skills(explicit_root)
        if not skills:
            raise ImportErrorWithHint(f"No skills were found in repository source: {source_label}")
        if import_mode == "all":
            return skills
        if import_mode == "one":
            if skill_path and is_skill_dir(explicit_root):
                return [explicit_root]
            if len(skills) == 1:
                return skills
            names = ", ".join(path.name for path in skills)
            raise ImportErrorWithHint(
                f"Repository source contains multiple skills ({names}). Specify --skill-path or switch to --import-mode all."
            )
        if len(skills) == 1:
            return skills
        names = ", ".join(path.name for path in skills)
        raise ImportErrorWithHint(
            f"Unable to infer whether to import one or all skills from repository source ({names}). "
            "Specify --import-mode one|all, and provide --skill-path if importing one skill."
        )

    if is_skill_dir(explicit_root):
        if import_mode == "all":
            raise ImportErrorWithHint("Source resolves to a single skill. --import-mode all is not applicable.")
        return [explicit_root]

    skills = scan_for_skills(explicit_root)
    if not skills:
        raise ImportErrorWithHint(f"No skills were found in source: {source_label}")
    if import_mode == "all":
        return skills
    if import_mode == "one":
        if skill_path and is_skill_dir(explicit_root):
            return [explicit_root]
        if len(skills) == 1:
            return skills
        names = ", ".join(path.name for path in skills)
        raise ImportErrorWithHint(
            f"Source contains multiple skills ({names}). Specify --skill-path or switch to --import-mode all."
        )
    if len(skills) == 1:
        return skills
    names = ", ".join(path.name for path in skills)
    raise ImportErrorWithHint(
        f"Source could be a multi-skill repository ({names}). Specify --source-kind repo and --import-mode all|one."
    )


def copy_skill_tree(source_dir: Path, dest_dir: Path, replace: bool) -> None:
    if dest_dir.exists():
        if not replace:
            raise ImportErrorWithHint(f"Destination already exists: {dest_dir}. Re-run with --replace if needed.")
        shutil.rmtree(dest_dir)

    def ignore(_: str, names: list[str]) -> set[str]:
        ignored = set()
        for name in names:
            if name in FORBIDDEN_COPY_NAMES:
                ignored.add(name)
                continue
            if Path(name).suffix in FORBIDDEN_COPY_SUFFIXES:
                ignored.add(name)
        return ignored

    shutil.copytree(source_dir, dest_dir, ignore=ignore)


def normalize_skill(dest_dir: Path, dest_name: str, pack_name: str, source_label: str) -> tuple[str, str]:
    skill_md_path = dest_dir / "SKILL.md"
    if not skill_md_path.exists():
        raise ImportErrorWithHint(f"Imported directory is missing SKILL.md: {dest_dir}")

    text = skill_md_path.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(text)
    description = frontmatter.get("description") or summarize_description(body)
    title = read_markdown_title(body) or dest_name.replace("-", " ").title()

    skill_md_path.write_text(
        render_frontmatter({"name": dest_name, "description": description}, body),
        encoding="utf-8",
    )

    existing_manifest = load_json(dest_dir / "skill.json")
    tags = list(dict.fromkeys([*(existing_manifest.get("tags") or []), *DEFAULT_TAGS]))
    manifest = {
        "name": dest_name,
        "title": existing_manifest.get("title") or title,
        "description": existing_manifest.get("description") or description,
        "owners": DEFAULT_OWNERS,
        "tags": tags,
        "agents": existing_manifest.get("agents") or DEFAULT_AGENTS,
        "pack": pack_name,
        "status": "draft",
        "source": source_label,
    }
    save_json(dest_dir / "skill.json", manifest)
    return manifest["title"], manifest["description"]


def update_pack(hub_root: Path, pack_name: str, skill_name: str) -> Path:
    pack_path = hub_root / "packs" / f"{pack_name}-pack.json"
    if not pack_path.exists():
        raise ImportErrorWithHint(f"Pack file not found: {pack_path}")

    pack = load_json(pack_path)
    skills = pack.get("skills") or []
    if skill_name not in skills:
        skills.append(skill_name)
        pack["skills"] = skills
        save_json(pack_path, pack)
    return pack_path


def ensure_branch(hub_root: Path, branch_name: str | None) -> str | None:
    if not branch_name:
        return None

    current_branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=hub_root)
    if current_branch != branch_name:
        existing = run_git(["branch", "--list", branch_name], cwd=hub_root)
        if existing:
            run_git(["checkout", branch_name], cwd=hub_root)
        else:
            run_git(["checkout", "-b", branch_name], cwd=hub_root)
    return branch_name


def commit_and_push(hub_root: Path, push: bool, branch_name: str | None) -> None:
    run_git(["add", "skills", "packs"], cwd=hub_root)
    status = run_git(["status", "--short"], cwd=hub_root)
    if not status:
        return
    run_git(["commit", "-m", "feat: import third-party skill(s)"], cwd=hub_root)
    if push:
        if branch_name:
            run_git(["push", "-u", "origin", branch_name], cwd=hub_root)
        else:
            run_git(["push"], cwd=hub_root)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import third-party skill(s) into Drew Grant Skills Hub.")
    parser.add_argument("source", help="Local directory, repository URL, or direct directory URL")
    parser.add_argument(
        "--source-kind",
        choices=["auto", "skill", "repo"],
        default="auto",
        help="Whether the source should be treated as a single skill or a repository containing one or more skills",
    )
    parser.add_argument(
        "--import-mode",
        choices=["auto", "one", "all"],
        default="auto",
        help="Import one skill or all skills from the source",
    )
    parser.add_argument(
        "--workspace-dir",
        help="Temporary workspace root. Defaults to a dedicated .tmp-import-third-party-skill-* directory in the current directory",
    )
    parser.add_argument(
        "--skill-path",
        help="Relative path to a single skill or a subdirectory to scan inside the source repo, e.g. skills/foo or review",
    )
    parser.add_argument("--hub-dir", help="Existing local hub repository root")
    parser.add_argument(
        "--dest-name",
        help="Destination skill directory name. Only valid when exactly one skill is imported",
    )
    parser.add_argument("--pack", default=DEFAULT_PACK, help="Target pack name, default: foundation")
    parser.add_argument("--replace", action="store_true", help="Replace destination skill if it already exists")
    parser.add_argument("--commit", action="store_true", help="Create a git commit after import")
    parser.add_argument("--push", action="store_true", help="Push after import; implies --commit")
    parser.add_argument("--branch-name", help="Create/switch to a branch before commit, e.g. feat/import-foo")
    parser.add_argument("--keep-temp", action="store_true", help="Keep temporary directories after completion")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args.commit = args.commit or args.push

    workspace_parent = Path(args.workspace_dir).expanduser().resolve() if args.workspace_dir else Path.cwd()
    temp_root = create_workspace_dir(workspace_parent)
    created_hub_clone = False

    try:
        if args.hub_dir:
            hub_root = Path(args.hub_dir).expanduser().resolve()
        else:
            hub_root = find_hub_root(Path.cwd()) or None

        if hub_root is None:
            hub_root = temp_root / "skills-hub"
            clone_repo(HUB_REPO_URL, hub_root)
            created_hub_clone = True

        if not (hub_root / "skills").exists() or not (hub_root / "packs").exists():
            raise ImportErrorWithHint(f"Invalid hub repository: {hub_root}")

        source_root, source_label = resolve_source_root(args.source, temp_root)
        source_skill_dirs = choose_skill_paths(
            source_root=source_root,
            source_label=source_label,
            source_kind=args.source_kind,
            import_mode=args.import_mode,
            skill_path=args.skill_path,
        )

        if args.dest_name and len(source_skill_dirs) != 1:
            raise ImportErrorWithHint("--dest-name can only be used when importing exactly one skill.")

        imported: list[tuple[str, str, Path]] = []
        pack_path: Path | None = None

        for source_dir in source_skill_dirs:
            dest_name = sanitize_name(args.dest_name or source_dir.name)
            dest_dir = hub_root / "skills" / dest_name
            copy_skill_tree(source_dir, dest_dir, replace=args.replace)
            title, _ = normalize_skill(dest_dir, dest_name, args.pack, source_label)
            pack_path = update_pack(hub_root, args.pack, dest_name)
            imported.append((dest_name, title, dest_dir))

        branch = ensure_branch(hub_root, args.branch_name if args.commit else None)
        if args.commit:
            commit_and_push(hub_root, args.push, branch)

        print(f"Imported count: {len(imported)}")
        print(f"Source: {source_label}")
        print(f"Workspace directory: {temp_root}")
        print(f"Hub repository: {hub_root}")
        if pack_path:
            print(f"Pack updated: {pack_path}")
        for name, title, dest_dir in imported:
            print(f"- {name}: {title} -> {dest_dir}")
        if branch:
            print(f"Git branch: {branch}")

        if created_hub_clone and not args.push:
            print("Temporary hub clone was kept because changes were not pushed.")
            print(f"Continue work in: {hub_root}")
            return 0

        if args.keep_temp:
            print(f"Temporary workspace kept at: {temp_root}")
            return 0

        shutil.rmtree(temp_root, ignore_errors=True)
        return 0
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.strip() if exc.stderr else str(exc)
        print(f"Git command failed: {message}")
        print(f"Workspace directory: {temp_root}")
        return 1
    except ImportErrorWithHint as exc:
        print(f"Import failed: {exc}")
        print(f"Workspace directory: {temp_root}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
