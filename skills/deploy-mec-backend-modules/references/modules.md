# Supported Modules

Use this mapping to resolve local artifacts and remote deployment directories.
If the requested module is not listed here, do not guess.

## Full Deployment Set

When the user requests all modules, deploy this fixed set in order:

1. `mec-auth-server`
2. `mec-gateway`
3. `mec-platform`
4. `mec-system`
5. `mec-management`
6. `mec-collaborative-design`
7. `mec-ai-race`

| Module | Local artifact | Remote dir | Remote jar | Notes |
| --- | --- | --- | --- | --- |
| `mec-ai-race` | `mec-ai-race/target/mec-ai-race-0.0.1-SNAPSHOT-exec.jar` | `/soft/mec/airace` | `mec-ai-race-0.0.1-SNAPSHOT-exec.jar` | Remote inventory confirmed on 2026-04-10 |
| `mec-auth-server` | `mec-auth-server/target/mec-auth-server-0.0.1-SNAPSHOT.jar` | `/soft/mec/authserver` | `mec-auth-server-0.0.1-SNAPSHOT.jar` | Remote inventory confirmed on 2026-04-10 |
| `mec-collaborative-design` | `mec-collaborative-design/target/mec-collaborative-design-0.0.1-SNAPSHOT-exec.jar` | `/soft/mec/cd` | `mec-collaborative-design-0.0.1-SNAPSHOT-exec.jar` | Remote inventory confirmed on 2026-04-10 |
| `mec-gateway` | `mec-gateway/target/mec-gateway-0.0.1-SNAPSHOT.jar` | `/soft/mec/gateway` | `mec-gateway-0.0.1-SNAPSHOT.jar` | Remote inventory confirmed on 2026-04-10 |
| `mec-management` | `mec-management/target/mec-management-0.0.1-SNAPSHOT.jar` | `/soft/mec/management` | `mec-management-0.0.1-SNAPSHOT.jar` | Remote inventory confirmed on 2026-04-10 |
| `mec-platform` | `mec-platform/target/mec-platform-0.0.1-SNAPSHOT.jar` | `/soft/mec/platform` | `mec-platform-0.0.1-SNAPSHOT.jar` | Remote inventory confirmed on 2026-04-10 |
| `mec-system` | `mec-system/target/mec-system-0.0.1-SNAPSHOT.jar` | `/soft/mec/system` | `mec-system-0.0.1-SNAPSHOT.jar` | Remote inventory confirmed on 2026-04-10 |

## Notes

- This MEC backend project must be built with JDK 1.8. Before invoking Maven, set `JAVA_HOME` to `C:\Program Files\Java\jdk1.8.0_102` and prepend `C:\Program Files\Java\jdk1.8.0_102\bin` to `Path` in the same shell command.
- Build from the current local checkout instead of a fixed repository path.
- Build the full project by default with `$env:JAVA_HOME='C:\Program Files\Java\jdk1.8.0_102'; $env:Path='C:\Program Files\Java\jdk1.8.0_102\bin;' + $env:Path; C:\zhuge\code\apache-maven-3.6.3\bin\mvn.cmd clean install -DskipTests "-Dmaven.repo.local=C:\zhuge\code\repository"`.
- Before replacing a jar, confirm the remote directory contains the expected module files.
- If the local `target/` output name differs from this table, trust the freshly built artifact name but keep the confirmed remote directory.
- The current node also contains `/soft/mec/ai`, `/soft/mec/authserver_v1`, and `/soft/mec/sentinel`, but those are not part of this skill.
