# Drew Grant Skills Hub

This repository is Drew Grant's public skills source. It keeps a small, portable set of skills that can be installed through existing agent ecosystems without relying on private protocols.

Repository:

- Web: `https://github.com/happydrew/drewskills`
- Clone: `https://github.com/happydrew/drewskills.git`

## Canonical Structure

```text
skills/         canonical skills source
packs/          logical skill packs
docs/           minimal usage and maintenance docs
scripts/        validation and scaffolding
AGENTS.md       repository-level guidance
hub.json        repository-level metadata
```

## Install

Install the whole source for Claude Code:

```bash
npx skills add https://github.com/happydrew/drewskills.git --agent claude-code -g --yes
```

Install the whole source for Codex:

```bash
npx skills add https://github.com/happydrew/drewskills.git --agent codex -g --yes
```

Install the whole source for a universal installer:

```bash
npx openskills install https://github.com/happydrew/drewskills.git --universal -y
```

Install a single skill with `npx skills`:

```bash
npx skills add https://github.com/happydrew/drewskills.git --agent codex -g --skill import-third-party-skill --yes
```

## Included Skills

- `git-commit-and-push`
- `import-third-party-skill`
- `playwright-mcp-setup-windows`

## Maintenance

```powershell
python .\scripts\validate_registry.py
```

## Docs

- `docs/03-用户手册.md`
- `docs/04-技能开发与贡献手册.md`
