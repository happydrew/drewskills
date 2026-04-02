# Repository Targets

- Skills Hub web: `https://github.com/happydrew/drewskills`
- Skills Hub clone: `https://github.com/happydrew/drewskills.git`
- Canonical destination: `skills/<skill-name>/`
- Default pack: `packs/foundation-pack.json`

Import rules:

- Always land imported skills under `skills/`
- Prefer preserving the third-party skill body, but normalize `SKILL.md` frontmatter and `skill.json`
- Do not copy `.git`, install outputs, caches, or credentials into the imported skill
- Do not put local absolute paths in examples, references, or generated skill content
