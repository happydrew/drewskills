---
name: feishu-sheets-toolkit
description: Read, search, and write Feishu Sheets from natural-language user requests. Use when the user shares a Feishu spreadsheet link or asks things like "read this sheet", "search this spreadsheet", "find which sheet contains a keyword", "write these rows into the sheet", or "update a Feishu table". If credentials are not configured yet, ask the user for Feishu App ID and App Secret, explain that they are required for first-time setup, and initialize the local skill config before running any operation.
---

# Feishu Sheets Toolkit

Use this skill when the user is describing a Feishu spreadsheet task in plain language. The user does not need to know `sheetId`, `rangeSpec`, command names, or SDK details.

## Workflow

1. Identify the spreadsheet URL from the user's message.
2. Translate the user's request into one of these intents:
   - Read spreadsheet info
   - List all sheets
   - Read a specific range
   - Search within one sheet
   - Search across the whole spreadsheet
   - Write values into a range
3. Check whether local credentials exist at `.local/credentials.json`.
4. If credentials are missing, do not expose implementation details first. Ask the user in plain language for:
   - Feishu App ID
   - Feishu App Secret
   Explain briefly that these are needed only for first-time authorization.
5. After the user provides them, initialize the local config with:

```powershell
node scripts/bootstrap.mjs setup --app-id "<APP_ID>" --app-secret "<APP_SECRET>"
```

6. Run all operations through `node scripts/bootstrap.mjs ...`.
   The bootstrap script installs npm dependencies on first use if they are missing.
7. Prefer these commands:
   - `info`
   - `sheets`
   - `read`
   - `search-sheet`
   - `search-all`
   - `write`

## Natural-Language Triggers

This skill should trigger for user requests like:

- "Read this Feishu sheet for me"
- "Look at this spreadsheet and tell me what tabs it has"
- "Search this table for `youtube downloader`"
- "Find which sheet contains `qwen`"
- "Read rows 1 to 20 from this sheet"
- "Write these values into the daily keyword sheet"
- "Update this Feishu spreadsheet with these two rows"

Do not require the user to speak in code terms such as `sheetId`, `rangeSpec`, `CLI`, or `JSON matrix` unless follow-up clarification is truly necessary.

## User-Facing Interaction Rules

- Speak in plain language.
- Treat the user's input as a task request, not as a command specification.
- When you need missing information, ask only for the minimum required detail.
- If a write target is ambiguous, ask which sheet and where to write.
- If credentials are missing, ask for App ID and App Secret plainly and explain why.
- Do not ask the user to study code or command syntax.
- Only surface exact commands when useful for local terminal execution or explicit debugging.

## Command Rules

- Never hardcode credentials into SKILL.md, committed config, or source files.
- Store credentials only in the skill-local file `.local/credentials.json`.
- Do not print the secret back to the user after setup.
- Before writing, read the target range when practical to avoid accidental overwrites.
- After writing, read back the written range to confirm the change.
- If a write succeeds but immediate readback is stale, wait a few seconds and retry once.

## Intent Mapping

Map natural-language requests to operations like this:

- "What sheets are in this spreadsheet?"
  Use `sheets`
- "Read this part of the sheet"
  Use `read`
- "Search this one sheet for a keyword"
  Use `search-sheet`
- "Search the whole spreadsheet"
  Use `search-all`
- "Write these rows into this sheet"
  Use `write`

Read [references/commands.md](references/commands.md) for concrete examples and command syntax.

## Quick Commands

Use these command forms when terminal execution is needed:

```powershell
node scripts/bootstrap.mjs info --url "<FEISHU_SHEET_URL>"
node scripts/bootstrap.mjs sheets --url "<FEISHU_SHEET_URL>"
node scripts/bootstrap.mjs read --url "<FEISHU_SHEET_URL>" --range "<sheetId>!A1:C5"
node scripts/bootstrap.mjs search-sheet --url "<FEISHU_SHEET_URL>" --sheet "<sheetId-or-title>" --query "keyword"
node scripts/bootstrap.mjs search-all --url "<FEISHU_SHEET_URL>" --query "keyword" --mode exact
node scripts/bootstrap.mjs write --url "<FEISHU_SHEET_URL>" --range "<sheetId>!A1:B2" --values-file "<path-to-json>"
```

Read [references/commands.md](references/commands.md) for detailed command syntax and examples.

## Resources

- Read [references/commands.md](references/commands.md) for detailed usage, natural-language examples, and validation steps.
- Use `scripts/bootstrap.mjs` as the single entry point.
- Use `scripts/cli.mjs` and `scripts/lib/*.mjs` for the implementation.
