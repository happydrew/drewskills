# Example Commands

Import a direct single-skill URL:

```bash
python scripts/import_skill.py https://github.com/example/agent-skills/tree/main/skills/my-skill --source-kind skill --import-mode one
```

Import a top-level directory URL that itself is a skill:

```bash
python scripts/import_skill.py https://github.com/example/agent-skills/tree/main/review --source-kind skill --import-mode one
```

Import one skill from a repository URL:

```bash
python scripts/import_skill.py https://github.com/example/agent-skills.git --source-kind repo --import-mode one --skill-path skills/my-skill --hub-dir /path/to/local/drewskills
```

Import all skills from a multi-skill repository:

```bash
python scripts/import_skill.py https://github.com/example/agent-skills.git --source-kind repo --import-mode all
```

Replace an existing skill and create a commit:

```bash
python scripts/import_skill.py https://github.com/example/agent-skills/tree/main/skills/my-skill --source-kind skill --import-mode one --replace --commit --branch-name feat/import-my-skill
```

Run from any directory, clone the hub temporarily, then push and clean up:

```bash
python scripts/import_skill.py https://github.com/example/agent-skills.git --source-kind repo --import-mode all --push
```

Use a dedicated temporary workspace parent directory:

```bash
python scripts/import_skill.py https://github.com/example/agent-skills/tree/main/review --source-kind skill --import-mode one --workspace-dir /path/to/temp-workspace
```
