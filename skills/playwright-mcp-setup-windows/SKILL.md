---
name: playwright-mcp-setup-windows
description: Install, repair, and validate the official @playwright/mcp browser automation environment on Windows for Codex. Default to local Chrome, English browser locale, and two MCP entries for temporary and fixed user-data-dir workflows. Use when the user asks to install, configure, fix, bootstrap, or verify Playwright MCP, local Chrome browser automation, temp/fixed profile setup, English browser defaults, or browser capability initialization in a new agent environment. Do not use for routine day-to-day browsing tasks once the environment is already working.
---

# Playwright MCP Setup Windows

## Purpose

This skill is for environment bootstrap, repair, and validation.
It is not the skill for routine browser operation after setup is complete.

Its job is to turn a Windows Codex environment into a reusable Playwright MCP baseline with these defaults:

- official `@playwright/mcp`
- local Chrome
- English browser locale by default
- two MCP entries:
  - `playwright-temp-userdir`
  - `playwright-fixed-userdir`
- verified browsing and interaction

The runtime browsing work should happen through the MCP tools themselves.
This skill exists to install and maintain the environment those tools depend on.

## Why This Baseline

The skill should standardize a setup that has proven practical and stable across Windows machines:

- local Chrome is usually more stable and closer to real user browsing than a generic bundled browser path
- English browser defaults reduce language-dependent UI variance during automation
- a temporary profile entry is safer for parallel Codex windows and one-off tasks
- a fixed profile entry is better for login persistence and session reuse
- a dedicated MCP profile is safer than using the user's daily Chrome profile
- a fresh-process verification step catches real configuration problems instead of trusting the current session state

## When To Use

Use this skill when the user wants any of the following:

- install Playwright MCP
- configure browser automation for Codex on Windows
- make Codex use local Chrome
- set up `playwright-temp-userdir` and `playwright-fixed-userdir`
- make the Playwright browser default to English
- repair a broken Playwright MCP setup
- validate browser capability in a new or changed environment

Do not use this skill for normal browsing work once the environment is already healthy.

## References

Read [setup-guide.md](references/setup-guide.md) for the configuration architecture, defaults, and validation standard.

## Scripts

Use the bundled scripts rather than retyping the same logic:

- `scripts/check-env.ps1`
  - checks whether `codex`, `node`, `npx`, and Chrome are available
  - reports the status of the recommended MCP entries
- `scripts/configure-mcp.ps1`
  - with no arguments, installs or repairs both recommended MCP entries
  - can also repair or create a single named entry
  - defaults to local Chrome, English locale, and the recommended profile modes
- `scripts/verify-mcp.ps1`
  - by default verifies both recommended MCP entries in fresh `codex exec` processes
  - checks English locale, page navigation, and basic interaction

## Workflow

### 1. Inspect first

Always start with:

```powershell
powershell -ExecutionPolicy Bypass -File "<skill-dir>\scripts\check-env.ps1"
```

Read the result before deciding whether to install or repair.

### 2. Decide whether to install, repair, or stop

If any of these are missing, the environment is not ready:

- `codex`
- `node`
- `npx`
- Chrome executable

If the recommended Playwright MCP entries are absent, install them.
If they exist but do not match the baseline, repair them.
If they already match the baseline, do not reconfigure unless the user explicitly wants a reset.

### 3. Configure the MCP entries

Default install or repair:

```powershell
powershell -ExecutionPolicy Bypass -File "<skill-dir>\scripts\configure-mcp.ps1"
```

This should produce the recommended pair:

- `playwright-temp-userdir`
- `playwright-fixed-userdir`

Default behavior of the configuration script:

- finds a common local Chrome path automatically when possible
- uses official `@playwright/mcp@latest`
- defaults browser locale to `en-US`
- creates a temporary-profile entry and a fixed-profile entry
- uses a dedicated fixed profile directory instead of the daily Chrome profile
- sets a larger navigation timeout
- sets a fixed viewport, defaulting to `1600x900`

Single-entry override is allowed when the environment needs a custom name or mode:

```powershell
powershell -ExecutionPolicy Bypass -File "<skill-dir>\scripts\configure-mcp.ps1" -McpName my-playwright-temp -ProfileMode temporary
```

### 4. Verify in a fresh process

After install or repair, validate with:

```powershell
powershell -ExecutionPolicy Bypass -File "<skill-dir>\scripts\verify-mcp.ps1"
```

This matters because a fresh `codex exec` process re-reads MCP configuration and is a better validation surface than trusting the current interactive session state.

### 5. Report the boundary clearly

If configuration succeeds, tell the user:

- which MCP entries are now installed
- whether verification passed
- whether a new Codex session is recommended before routine use

Do not claim that the current running Codex session will always hot-load the new MCP.

## Default Policy

Use these defaults unless the user asks otherwise:

- official `@playwright/mcp`
- local Chrome
- English locale (`en-US`)
- `playwright-temp-userdir` for isolated and parallel-safe work
- `playwright-fixed-userdir` for reusable state
- no stealth flags
- no user-agent spoofing
- no attempt to modify the user's daily Chrome profile

## Non-Goals

This skill is not for:

- bypassing anti-bot systems
- promising undetectable automation
- replacing normal browser-operation prompts once setup is complete
- using the user's everyday Chrome profile by default

## If The User Wants Stronger Session Reuse

Only after the baseline works, discuss the official `--extension` route as a later-phase upgrade.
Do not switch to extension mode by default during first-time setup unless the user explicitly asks for it.
