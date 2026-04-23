# Target Server

- Host: `121.237.182.143`
- SSH port: `60022`
- Alias: `182.143`
- Remote user: `root`
- Base deployment directory: `/soft/mec`

## Confirmed Service Inventory

The current node inventory under `/soft/mec` includes:

- `airace`
- `authserver`
- `authserver_v1`
- `cd`
- `gateway`
- `management`
- `platform`
- `system`
- `ai`
- `sentinel`

This skill currently manages only the MEC backend service directories documented in [modules.md](modules.md).

## Access Rule

The local environment is expected to have passwordless SSH configured only for remote `root`.
Always verify SSH connectivity on the first remote operation in a conversation:

```powershell
ssh -o BatchMode=yes -o ConnectTimeout=5 -p 60022 root@121.237.182.143 "echo connected"
```

If the check fails, stop operational work and tell the user that passwordless SSH is not configured for `root@121.237.182.143:60022`.
