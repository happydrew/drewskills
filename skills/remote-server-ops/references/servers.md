# Server Inventory

Keep this file concise and update it when new nodes are confirmed.

Unless explicitly noted otherwise, execute remote SSH commands on all servers in this inventory as user `root`.

Current access note: the local environment currently has passwordless SSH configured only for the remote `root` user on collected servers. Therefore, all routine remote access in this skill should use `root@<host>` unless a server-specific exception is added later.

## Known Servers

- `220.154.135.77`
  SSH port: `60022`
  Name: `da-model-platform-backend`
  Environment: `shengchan`
  Role: Large model service platform backend.

- `121.237.182.143`
  SSH port: `60022`
  Name: `machinery-cloud-backend`
  Environment: `shengchan`
  Role: Machinery cloud backend.

- `121.229.145.169`
  SSH port: `60022`
  Name: `postgres-es`
  Environment: `shengchan`
  Role: PostgreSQL host and Elasticsearch-related services.

- `121.237.182.142`
  SSH port: `60022`
  Name: `minio`
  Environment: `shengchan`
  Role: MinIO host.

- `10.7.121.106`
  SSH port: `22`
  Name: `backend-env`
  Environment: `ceshi`
  Role: Backend test environment.

- `10.7.121.105`
  SSH port: `22`
  Name: `frontend-env`
  Environment: `ceshi`
  Role: Frontend test environment.

- `10.7.128.10`
  SSH port: `22`
  Name: `postgresql`
  Environment: `ceshi`
  Default user: `root`
  Role: PostgreSQL server.

## Reminder

On the first operation against any node in the current conversation, verify passwordless SSH access before substantive work.
