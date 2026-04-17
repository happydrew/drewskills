# Setup Guide

## Scope

This skill standardizes a Windows browser-automation baseline for Codex.

The baseline is:

- official `@playwright/mcp`
- local Chrome instead of a generic bundled browser path
- persistent profile instead of isolated one-off sessions

## Why This Baseline

These defaults usually produce a better starting point for real browsing work:

- local Chrome is closer to the browser a user actually runs
- a persistent profile allows state to survive across sessions
- the configuration is stable and easy to validate

This is a setup strategy, not a guarantee against detection or challenges.

## Baseline MCP Arguments

Recommended argument shape:

```text
powershell -ExecutionPolicy Bypass -File <launch-script>
-ChromePath <chrome-path>
-ProfileDir <persistent-profile-dir>
-NavigationTimeoutMs 90000
```

The launch script then starts:

```text
npx -y @playwright/mcp@latest
--browser chrome
--executable-path <chrome-path>
--user-data-dir <persistent-profile-dir>
--timeout-navigation 90000
--viewport-size 1600x900
```

If you pass `-ViewportSize`, that fixed size is used instead of the default `1600x900`.

## Why Not Use The Daily Chrome Profile

Do not default to the user's main Chrome profile.

Reasons:

- easier to debug
- lower risk of corrupting or polluting the user's normal browser state
- easier to reset

Use a separate persistent profile directory instead.

## Verification Standard

A configuration is considered healthy only if all of these pass:

1. MCP entry exists in `codex mcp list`
2. `codex mcp get playwright` shows the expected command shape
3. A fresh `codex exec` process can:
   - browse a normal web page
   - read title/text
   - perform a simple input-and-click interaction

Optional:

- validate a real target site such as Google Trends if the user specifically cares about that site

## Upgrade Path

Once the baseline works, a second-phase option is:

- official `--extension` mode

Use that only when the user explicitly wants stronger reuse of an existing Chrome session or browser state.
