# Mission: simplex-alerter

simplex-alerter is a FastAPI webhook bridge that forwards alerts from external monitoring services (Grafana, Sonarr/Servarr, Forgejo) into SimpleX Chat groups on the homeserver (`pi`).

## Core value
- Single reliable alert delivery path for all homeserver services via SimpleX Chat
- Dead man's switch capability for user liveness monitoring
- Zero external SaaS dependencies

## Deployment targets
- Native NixOS systemd service on `homeserver` (pi) — port 3334 — used by monitoring/Grafana/DR tests
- Docker container within servarr compose stack on `homeserver` — port 7898 — used by Sonarr/Radarr/Bazarr webhooks

## Non-goals
- Multi-tenant or cloud-hosted deployment
- Support for alert sources beyond the defined KnownModels union
