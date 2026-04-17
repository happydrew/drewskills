---
name: playwright-mcp-setup-windows
description: Install, repair, and validate the official @playwright/mcp browser automation environment on Windows for Codex. Default to local Chrome plus a persistent profile so browser behavior is closer to a real user session. Use when the user asks to install, configure, fix, bootstrap, or verify Playwright MCP, local Chrome browser automation, persistent browser profile setup, or browser capability initialization in a new agent environment. Do not use for routine day-to-day browsing tasks once the environment is already working.
---

# Playwright MCP Setup Windows

## Purpose

This skill is for environment bootstrap and repair, not for routine browsing.

Its job is to make a Windows Codex environment ready to use the official `@playwright/mcp` with:

- local Chrome
- a persistent browser profile
- a verified browsing and interaction path

Default to the official MCP route first.
Default to local Chrome plus a persistent profile.
Treat extension attachment as a later upgrade path, not the initial baseline.

## When To Use

Use this skill when the user wants any of the following:

- install Playwright MCP
- configure browser automation for Codex
- make Codex use local Chrome
- set up a persistent browser profile
- repair a broken Playwright MCP setup
- validate browser capability in a new agent environment

Do not use this skill for normal browsing work if the browser environment is already installed and healthy.

## References

Read [setup-guide.md](references/setup-guide.md) for the default architecture, parameter choices, and validation strategy.

## Scripts

Use the bundled scripts rather than retyping the same logic:

- `scripts/check-env.ps1`
  - checks whether `codex`, `node`, `npx`, Chrome, and Playwright MCP are available
  - reports the current MCP configuration state
- `scripts/configure-mcp.ps1`
  - installs or repairs the `playwright` MCP entry
  - defaults to local Chrome and a persistent profile
- `scripts/verify-mcp.ps1`
  - runs smoke tests through a fresh `codex exec` process
  - verifies both browsing and basic interaction

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

If the `playwright` MCP entry is absent, install it.
If the entry exists but does not use the official `@playwright/mcp` route with local Chrome and a persistent profile, repair it.
If the entry already matches the expected baseline, skip reconfiguration unless the user explicitly wants a reset.

### 3. Configure the MCP

Run:

```powershell
powershell -ExecutionPolicy Bypass -File "<skill-dir>\scripts\configure-mcp.ps1"
```

Default behavior of the configuration script:

- chooses a common Windows Chrome path automatically when possible
- uses MCP name `playwright`
- uses official `@playwright/mcp@latest`
- uses `--browser chrome`
- uses a persistent profile directory
- sets a larger navigation timeout
- sets a fixed viewport

If the script cannot find Chrome automatically, stop and ask the user for the Chrome executable path.

### 4. Verify in a fresh process

After install or repair, validate with:

```powershell
powershell -ExecutionPolicy Bypass -File "<skill-dir>\scripts\verify-mcp.ps1"
```

This matters because a fresh `codex exec` process re-reads MCP configuration and is a better validation surface than trusting the current interactive session state.

### 5. Report the boundary clearly

If configuration succeeds, tell the user:

- whether the MCP entry is now installed
- whether smoke tests passed
- whether a new Codex session is recommended before routine use

Do not claim that the current running Codex session will always hot-load the new MCP.

## Default Policy

Use these defaults unless the user asks otherwise:

- official `@playwright/mcp`
- local Chrome
- persistent profile
- no stealth flags
- no user-agent spoofing
- no attempt to modify the user's daily Chrome profile

## Non-Goals

This skill is not for:

- bypassing anti-bot systems
- promising undetectable automation
- attaching to an existing browser session by default
- replacing normal browser-operation prompts once setup is complete

## If The User Wants Stronger Session Reuse

Only after the baseline is working, discuss the official `--extension` route as a second-phase upgrade.
Do not switch to extension mode by default during first-time setup unless the user explicitly asks for it.
