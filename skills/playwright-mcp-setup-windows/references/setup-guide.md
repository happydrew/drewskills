# Setup Guide

## Scope

This guide defines the Windows baseline that this skill should install, repair, and verify.

The baseline is:

- official `@playwright/mcp`
- local Chrome
- English browser locale by default
- two MCP entries:
  - `playwright-temp-userdir`
  - `playwright-fixed-userdir`

This guide is about setup and repair.
It is not the runtime operating guide for day-to-day browser actions after setup is complete.

## Why Local Chrome

Prefer local Chrome because it is usually:

- closer to the browser the user actually runs
- easier to reason about when debugging
- more stable for real browsing behavior on Windows

Avoid relying on the user's daily Chrome profile.
Use a separate MCP-specific profile directory instead.

## Why English Defaults

Prefer English defaults because they reduce language drift in:

- page button labels
- browser-exposed locale values
- automation prompts and debugging artifacts
- reproducibility across different Windows machines

The baseline should set both:

- Chrome launch language via `--lang=<locale>`
- Playwright context locale via `contextOptions.locale`

Default locale: `en-US`

## Why Two MCP Entries

The skill should standardize two distinct usage modes because one MCP entry is not enough for both needs.

### `playwright-temp-userdir`

Use for:

- parallel Codex windows
- one-off browsing tasks
- isolation between tasks
- avoiding profile-lock conflicts

Behavior:

- creates a unique temporary user-data-dir when the MCP process starts
- cleans it up when the MCP process exits

### `playwright-fixed-userdir`

Use for:

- persistent login state
- cookies and local storage reuse
- repeated work against the same sites

Behavior:

- uses a dedicated fixed profile directory
- should not share the user's daily Chrome profile
- should not be used concurrently by multiple Codex windows against the same directory

## Recommended Script Behavior

`configure-mcp.ps1` should, by default:

- install or repair `playwright-temp-userdir`
- install or repair `playwright-fixed-userdir`
- auto-detect local Chrome when possible
- default to `en-US`
- use a fixed viewport such as `1600x900`
- use a larger navigation timeout such as `90000`

Single-entry override is still useful, but the recommended no-argument path should set up both entries.

## Launch Strategy

The launcher should build a generated Playwright MCP config and then run:

```text
npx -y @playwright/mcp@latest
--config <generated-config-json>
--timeout-navigation 90000
--viewport-size 1600x900
```

The generated config should include:

- local Chrome executable path
- the resolved user-data-dir
- `launchOptions.args` including `--lang=en-US` by default
- `contextOptions.locale` set to `en-US` by default
- viewport values that match the chosen baseline

## Verification Standard

A configuration is considered healthy only if all of these pass:

1. `codex mcp list` shows the expected MCP entries
2. `codex mcp get playwright-temp-userdir` and `codex mcp get playwright-fixed-userdir` show the expected command shape
3. a fresh `codex exec` process can:
   - report `navigator.language` as `en-US`
   - browse a normal web page
   - read basic page content
   - perform a simple input and click interaction

Optional:

- validate a real target site such as Google Trends if the user specifically cares about that site

## Upgrade Path

Once the baseline works, later upgrades may include:

- official `--extension` mode
- alternate MCP names for special environments
- different fixed profile directories for multiple persistent slots

These are extensions to the baseline, not the baseline itself.
