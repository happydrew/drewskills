---
name: deploy-mec-backend-modules
description: Build and deploy one, multiple, or all supported MEC backend Maven modules from the current working tree to `121.237.182.143:60022`, upload jars into the confirmed `/soft/mec` service directories, restart services with the existing `start.sh`, and verify process status and `nohup.out`. Use when the user asks to publish, deploy, upload, replace, or restart `mec-ai-race`, `mec-auth-server`, `mec-collaborative-design`, `mec-gateway`, `mec-management`, `mec-platform`, or `mec-system` on node `182.143`.
---

# Deploy Mec Backend Modules

## Overview

Use this skill from whichever local `mec-backend` checkout is currently open. Do not assume a fixed local path or branch. Build from the current working directory and deploy only the requested modules.

Read [references/servers.md](references/servers.md) for the fixed target host and SSH rules.
Read [references/modules.md](references/modules.md) for supported module names, local artifact paths, actual remote directories, and jar names.

Use JDK 1.8 for all Maven builds in this project.
Set `JAVA_HOME` to `C:\Program Files\Java\jdk1.8.0_102` and prepend its `bin` directory in the same command before invoking Maven.
Do not rely on the current shell's default JDK because this repository may fail to compile under JDK 17.

Use Maven from `C:\zhuge\code\apache-maven-3.6.3`.
Use the local Maven repository `C:\zhuge\code\repository` for this workflow.

## Inputs

Accept module names in natural language.
Support one module or multiple modules separated by commas, Chinese commas, whitespace, or newlines.
Support full deployment requests such as `全部模块`, `全量发布`, `重新部署全部`, or `deploy all`.

Normalize module input before execution:

- Split on commas, Chinese commas, whitespace, and line breaks.
- Trim each item.
- Keep the original order.
- Deduplicate repeated modules.

If no supported module is identified, ask the user which module or modules to deploy.
If a requested module is not listed in [references/modules.md](references/modules.md), stop and tell the user it is not supported by this skill.

When the user requests all modules, expand to this fixed deployment order:

1. `mec-auth-server`
2. `mec-gateway`
3. `mec-platform`
4. `mec-system`
5. `mec-management`
6. `mec-collaborative-design`
7. `mec-ai-race`

## Workflow

### 1. Confirm local context

Assume the current working directory is the intended Maven multi-module checkout.
Do not switch directories to another clone unless the user explicitly asks.

### 2. Build the whole project

Build the full Maven project from the current working directory. Skip tests by default.
Always force JDK 1.8 in the build command instead of assuming the ambient Java version.

```powershell
$env:JAVA_HOME='C:\Program Files\Java\jdk1.8.0_102'
$env:Path='C:\Program Files\Java\jdk1.8.0_102\bin;' + $env:Path
C:\zhuge\code\apache-maven-3.6.3\bin\mvn.cmd clean install -DskipTests "-Dmaven.repo.local=C:\zhuge\code\repository"
```

Do not default to partial module builds because the project modules depend on each other.
If the build fails, stop and report the failing phase.

### 3. Verify SSH access on first contact

On the first remote operation in the current conversation, verify passwordless SSH access:

```powershell
ssh -o BatchMode=yes -o ConnectTimeout=5 -p 60022 root@121.237.182.143 "echo connected"
```

If passwordless SSH is unavailable, stop and tell the user that this workflow supports only `root` passwordless SSH.

### 4. Deploy modules sequentially

Deploy modules in user-specified order.
Use a stop-on-first-failure policy. If one module fails, do not continue with later modules.

For each module:

1. Resolve the local artifact path from [references/modules.md](references/modules.md).
2. Resolve the remote directory and target jar name from [references/modules.md](references/modules.md).
3. Confirm the remote directory exists.
4. Confirm `start.sh` exists in the remote directory.
5. Upload the new jar as `<jar>.new`.
6. Rename the old jar to `<jar>.bak-YYYYMMDD-HHMMSS` when it exists.
7. Move the uploaded jar into place.
8. Run `./start.sh restart`.
9. Verify `./start.sh status`, `ps`, and recent `nohup.out`.

### 5. Use direct remote commands

Prefer direct, inspectable commands.
Use `root` for all remote operations.
When environment initialization matters, prefer:

```powershell
ssh -p 60022 root@121.237.182.143 "bash -lc 'source /etc/profile >/dev/null 2>&1 || true; <command>'"
```

Typical commands:

```powershell
scp -P 60022 "<local-artifact>" root@121.237.182.143:<remote-dir>/<jar-name>.new
ssh -p 60022 root@121.237.182.143 "bash -lc 'cd <remote-dir> && ls -l && sed -n \"1,220p\" start.sh'"
ssh -p 60022 root@121.237.182.143 "bash -lc 'cd <remote-dir> && mv <jar-name> <jar-name>.bak-<timestamp> && mv <jar-name>.new <jar-name> && ./start.sh restart'"
ssh -p 60022 root@121.237.182.143 "bash -lc 'cd <remote-dir> && ./start.sh status && tail -n 80 nohup.out'"
```

When quoting becomes fragile, send a here-document over SSH standard input instead of deeply nested quotes.

## Validation

For each successfully deployed module, confirm all of the following:

- The remote process is running.
- `./start.sh status` returns success.
- `<module-dir>/nohup.out` exists and shows a normal startup signal such as `Started ...Application`, `Tomcat started`, or an equivalent ready message.

If restart returns success but the service is not healthy, treat the deployment as failed.

## Response Format

Summarize results per module in order and include:

- build result
- local artifact path
- remote directory
- uploaded artifact name
- backup artifact name when a previous jar existed
- restart result
- pid when available
- `nohup.out` verification result
- whether deployment stopped early because of a failure
