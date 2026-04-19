# Feishu Sheets Toolkit Commands

This file exists so the skill can translate plain-language requests into concrete actions. Start from the user's natural-language goal, not from the command line.

## First-Time Setup

If the user says something like:

- "Read this Feishu sheet"
- "Search this spreadsheet"
- "Write this into the table"

and the skill has no saved credentials yet, ask:

- "Please provide your Feishu App ID."
- "Please provide your Feishu App Secret."

Explain briefly:

- "I need these once to authorize access to your Feishu spreadsheet."

After the user provides them, run:

```powershell
node scripts/bootstrap.mjs setup --app-id "<APP_ID>" --app-secret "<APP_SECRET>"
```

Or if you are operating directly in the terminal with the user:

```powershell
node scripts/bootstrap.mjs setup
```

Credentials are stored only in:

```text
.local/credentials.json
```

## Natural-Language Examples

### 1. Read spreadsheet basics

User request:

- "Look at this spreadsheet and tell me what it is"

Action:

```powershell
node scripts/bootstrap.mjs info --url "https://.../sheets/<spreadsheetToken>?sheet=<sheetId>"
```

### 2. List all sheets

User request:

- "What tabs are in this spreadsheet?"
- "List all the sheets in this Feishu table"

Action:

```powershell
node scripts/bootstrap.mjs sheets --url "https://.../sheets/<spreadsheetToken>?sheet=<sheetId>"
```

### 3. Read a specific area

User request:

- "Read A1:C5 from 每日找词"
- "Show me the first 20 rows of this sheet"

Action:

- If the user gives a sheet name, first resolve it from `sheets`
- Then call `read`

```powershell
node scripts/bootstrap.mjs read --url "https://.../sheets/<spreadsheetToken>?sheet=<sheetId>" --range "<sheetId>!A1:C5"
```

### 4. Search within one sheet

User request:

- "Search 每日找词 for `qwen`"
- "Find `youtube downloader` in this tab"

Action:

```powershell
node scripts/bootstrap.mjs search-sheet --url "https://.../sheets/<spreadsheetToken>?sheet=<sheetId>" --sheet "<sheetId-or-title>" --query "keyword"
```

### 5. Search across the whole spreadsheet

User request:

- "Search this whole spreadsheet for `youtube downloader`"
- "Tell me which sheet contains `seedance`"

Action:

```powershell
node scripts/bootstrap.mjs search-all --url "https://.../sheets/<spreadsheetToken>?sheet=<sheetId>" --query "keyword" --mode exact
```

### 6. Write values

User request:

- "Write these two rows into 每日找词"
- "Put this small table into D1:E2"
- "Update this Feishu sheet with these values"

Action:

1. If the target sheet or range is unclear, ask a follow-up question.
2. Read the target range first when practical.
3. Convert the user data into a 2D array JSON file.
4. Run `write`.
5. Read back the same range to verify.

## Read Operations

Spreadsheet info:

```powershell
node scripts/bootstrap.mjs info --url "https://.../sheets/<spreadsheetToken>?sheet=<sheetId>"
```

List sheets:

```powershell
node scripts/bootstrap.mjs sheets --url "https://.../sheets/<spreadsheetToken>?sheet=<sheetId>"
```

Read a range:

```powershell
node scripts/bootstrap.mjs read --url "https://.../sheets/<spreadsheetToken>?sheet=<sheetId>" --range "<sheetId>!A1:C5"
```

## Search Operations

Search within one sheet:

```powershell
node scripts/bootstrap.mjs search-sheet --url "https://.../sheets/<spreadsheetToken>?sheet=<sheetId>" --sheet "<sheetId-or-title>" --query "keyword"
```

Search all sheets:

```powershell
node scripts/bootstrap.mjs search-all --url "https://.../sheets/<spreadsheetToken>?sheet=<sheetId>" --query "keyword" --mode exact
```

Supported search modes:

- `contains`
- `exact`
- `regex`

## Write Operations

Prepare a JSON matrix file:

```json
[["name","value"],["test_key","test_value"]]
```

Write it into a range:

```powershell
node scripts/bootstrap.mjs write --url "https://.../sheets/<spreadsheetToken>?sheet=<sheetId>" --range "<sheetId>!A1:B2" --values-file "tmp-write-values.json"
```

## Validation Pattern

For safe write validation:

1. Read the target range first.
2. Write the test matrix.
3. Read the same range again.
4. If stale, wait 2-5 seconds and read once more.
5. Run `search-sheet` if you need a semantic confirmation.
