---
name: docker-compose-helper
description: Use when generating, auditing, or hardening Docker Compose files for security issues — privileged containers, exposed ports, missing read-only mounts, unsafe network config, or secret handling problems.
---

# Docker Compose Helper

## Overview
Generate secure-by-default Compose configs and audit existing ones against common security mistakes.

## Audit Checklist

When auditing an existing compose file, check every service for:

| Check | Bad | Good |
|-------|-----|------|
| Privileged mode | `privileged: true` | Remove it; use specific caps |
| Capabilities | unset | `cap_drop: [ALL]` + add only what's needed |
| Read-only filesystem | unset | `read_only: true` + tmpfs for writable paths |
| User | unset (runs as root) | `user: "1000:1000"` or named user |
| Port exposure | `ports: "0.0.0.0:80:80"` | `ports: "127.0.0.1:80:80"` unless public |
| Network isolation | all services on default | separate networks per trust level |
| Secrets in env vars | `PASSWORD=secret` | use Docker secrets or env_file outside repo |
| Host mounts | `/:/host` or `/etc` mounts | minimal, specific paths only |
| Restart policy | `restart: always` (masks crashes) | `restart: unless-stopped` |

## Secure Template

```yaml
services:
  app:
    image: your-image:tag
    user: "1000:1000"
    read_only: true
    tmpfs:
      - /tmp
      - /var/run
    cap_drop:
      - ALL
    cap_add: []          # add only what's needed (e.g., NET_BIND_SERVICE)
    security_opt:
      - no-new-privileges:true
    ports:
      - "127.0.0.1:8080:8080"   # bind to localhost unless externally needed
    networks:
      - internal
    environment:
      - APP_ENV=production
    env_file:
      - .env             # keep secrets out of compose file
    restart: unless-stopped

networks:
  internal:
    driver: bridge
    internal: true       # no external internet access; remove for services that need it
```

## Common Cap Additions

Only add caps your service actually requires:

| Cap | Used for |
|-----|----------|
| `NET_BIND_SERVICE` | bind ports < 1024 |
| `CHOWN` | change file ownership on startup |
| `SETUID` / `SETGID` | drop privileges after start (e.g., nginx) |
| `DAC_OVERRIDE` | read files regardless of permissions |

## Generating a Compose File

Ask the user for:
1. What service (web app, database, reverse proxy, etc.)
2. What ports need external access vs. internal only
3. Any writable paths the container needs

Then generate from the template above, removing unneeded caps and adjusting tmpfs paths.

## Common Mistakes

- **Mounting Docker socket** (`/var/run/docker.sock`) gives container full host access — avoid or use a proxy (e.g., Tecnativa/docker-socket-proxy)
- **`network_mode: host`** bypasses all network isolation
- **Hardcoded secrets** in compose files get committed to git; use `.env` (in `.gitignore`) or Docker secrets
- **`latest` tags** are unpredictable; pin to a digest or version tag
