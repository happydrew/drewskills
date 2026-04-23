---
name: remote-server-ops
description: Execute remote operations, troubleshooting, deployment checks, process inspection, service restart, log analysis, configuration verification, and root-cause diagnosis on specified Linux servers over SSH. Use when the user names a server or node and asks for operations tasks such as starting or stopping services, checking ports, inspecting logs, verifying Nacos or database connectivity, diagnosing startup failures, or running shell commands remotely.
---

# Remote Server Ops

Execute all server operations through remote SSH shell commands. Treat this skill as a pragmatic Linux operations guide for production-like nodes.

Unless explicitly documented otherwise, execute remote SSH commands as `root` on all servers collected by this skill.

The current local machine is configured only for passwordless SSH login to the remote `root` account. Unless a server-specific exception is documented, always access collected servers as `root` and do not assume passwordless login exists for other remote users.

## Default Response

If the user invokes the skill without a concrete task, reply briefly in Chinese. A suitable example is:

`Wo shi yi ge yunwei xiao zhushou, qingwen you shenme yunwei renwu xuyao wo zhixing. Dangqian yi shoulu fuwuqi jian references/servers.md.`

Then list the collected server IPs and SSH ports from [references/servers.md](references/servers.md).

## Operating Rules

Require the user to specify the target server and the intended operations task when the request is ambiguous.

Perform all remote work through `ssh` and shell commands. Prefer direct, inspectable commands over hidden automation.

Use `root` as the default remote SSH user for all servers in [references/servers.md](references/servers.md) unless a server-specific exception is documented.

When explaining access methods or giving SSH examples, state explicitly that the local environment currently has passwordless SSH configured only for remote `root` users.

On the first operation against a server in the current conversation, check passwordless SSH access before any substantive work. Use a non-interactive probe such as:

```powershell
ssh -o BatchMode=yes -o ConnectTimeout=5 -p <port> root@<host> "echo connected"
```

If passwordless SSH is unavailable, stop operational work on that node, tell the user that passwordless SSH is not configured, and guide them to configure it. Give concrete commands appropriate for the local shell and remote account. A standard Linux-style flow is:

```bash
ssh-keygen -t ed25519
ssh-copy-id -p <port> root@<host>
ssh -p <port> root@<host>
```

When the local machine is Windows and `ssh-copy-id` is unavailable, provide a manual fallback:

```powershell
type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh -p <port> root@<host> "umask 077; mkdir -p ~/.ssh; cat >> ~/.ssh/authorized_keys"
```

After the first successful SSH probe for a node within the same conversation, do not repeat the probe unless connectivity appears to have changed.

## Execution Workflow

1. Identify the target server from the user request. If needed, consult [references/servers.md](references/servers.md).
2. On the first interaction with that node in the current conversation, verify passwordless SSH access.
3. Restate the task briefly in a commentary update and say what you will inspect first.
4. Run remote read-only inspection commands before making changes unless the user explicitly asks for an immediate operation.
5. When remote Java services depend on profile-based environment variables, prefer login-shell semantics or explicitly source common profiles before the target command.
6. Summarize findings, root cause, impact, and next actions concisely.
7. If the user asked only for diagnosis, discuss the cause and options before changing configuration or code.

## Remote Command Conventions

Prefer forms like:

```powershell
ssh -p <port> root@<host> "bash -lc 'source /etc/profile >/dev/null 2>&1 || true; <command>'"
```

Use `bash -lc` when environment initialization matters.

When quoting becomes fragile, send a script over standard input instead of deeply nested quotes.

Prefer read-only commands first:

```bash
ps -ef
ss -ltnp
tail -n 200 <logfile>
grep -Ei "<pattern>" <logfile>
find <path> -maxdepth <n>
curl -s ...
systemctl status <service>
docker ps
docker logs --tail 200 <container>
```

Prefer `rg` locally for searching project code or local artifacts before correlating with remote symptoms.

## Diagnosis Heuristics

For startup failures, correlate three layers:

1. Process and port state on the remote server
2. Runtime logs on the remote server
3. Local project code and configuration that explain the failure path

Typical checks:

- Java process exists or exits immediately
- Target port is or is not listening
- `nohup.out`, `logs/nohup.out`, or service-specific log files
- Dependent components such as Nacos, PostgreSQL, Redis, Elasticsearch, Docker containers, or file paths
- Effective startup script assumptions such as `JAVA_HOME`, `PATH`, `JAR_FILE_NAME`, `PROC_NAME`, and log paths

For Nacos-related issues, verify:

- Nacos main HTTP port `8848`
- Nacos gRPC port `9848` when clients use Nacos 2.x+
- Auth status, username/password, namespace, group, and service registration
- Whether the target namespace actually exists before assuming services registered there

For PostgreSQL connectivity issues, verify:

- Target host and port
- `pg_hba.conf`
- listening address
- database, schema, username, and SSL mode

For Elasticsearch compatibility issues, verify:

- actual product identity from `GET /`
- server version
- whether the endpoint is Elasticsearch or OpenSearch
- compatibility between Spring Boot / Spring Data Elasticsearch client and server media-type support

## Change Discipline

Do not make extra edits beyond the user request.

When touching deployment scripts, keep changes minimal and aligned with the user's stated pattern. If the user wants diagnosis only, do not change files before discussing the root cause.

Never assume a service is registered in a given Nacos namespace without checking namespaces first, then services in that namespace, then instances of the service.

## References

Read [references/servers.md](references/servers.md) for the current server inventory and node-specific notes collected from prior operations.
