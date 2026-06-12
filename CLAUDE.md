# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

All development is done inside a Nix dev shell. Enter it with:
```
nix develop
```

The dev shell provides `uv`, `ruff`, `pyright`, `bandit`, `statix`, `deadnix`, and Python 3.13.

**Run the app:**
```
uv run simplex-alerter -c config.yml
```

**Lint (Python):**
```
ruff check simplex-alerter/
```

**Type check:**
```
pyright simplex-alerter/
```

**Security scan:**
```
bandit -r simplex-alerter/simplex_alerter/
```

**Lint (Nix):**
```
statix check
deadnix .
```

**Build Nix package:**
```
nix build
```

**Build Docker image:**
```
nix build .#docker-image
```
Output is `result` (a `.tar.gz` loadable with `docker load`). The `Dockerfile` at the root is only for running the Nix build inside a container — it is not a standalone Docker build.

## Architecture

`simplex-alerter` is a FastAPI webhook bridge that forwards alerts from external services (Grafana, Sonarr/Servarr, Forgejo) into SimpleX Chat groups.

### Process model

At startup, the app:
1. Uses `pexpect` to spawn `simplex-chat` once for DB initialization (`chat.py:init_chat`)
2. Spawns `simplex-chat` again as a subprocess via `subprocess.Popen` for the runtime WebSocket server (port 7897 by default)
3. Connects to the `simplex-chat` WebSocket as a client (`simpx/client.py:ChatClient`)
4. Starts two background asyncio tasks: `monitor_channels` (reads incoming messages) and `deadmans_switch_notifier` (fires alerts on inactivity)
5. Joins any configured SimpleX groups via invite links

The FastAPI app listens on port 7898 (default). Each incoming webhook `POST /{endpoint}` is routed to the SimpleX group whose name matches `endpoint`.

### Key modules

- `simplex_alerter/webhook/__init__.py` — FastAPI app, startup/shutdown lifecycle, webhook route, Prometheus metrics endpoint
- `simplex_alerter/simpx/client.py` — `ChatClient`: async WebSocket client for the `simplex-chat` process, with corr_id-based request/response tracking
- `simplex_alerter/simpx/transport.py` — WebSocket transport layer
- `simplex_alerter/chat.py` — `init_chat` (pexpect DB init), `monitor_channels` (liveness tracking), `deadmans_switch_notifier` (dead man's switch loop)
- `simplex_alerter/config.py` — YAML config loader; config is a global singleton accessed via `get_config()`
- `simplex_alerter/webhook/request_models/` — Pydantic models per alert source; each has an async `render()` method returning a formatted string. Unknown payloads fall back to raw JSON.

### Config file structure

```yaml
bot_name: alertBot          # optional, overrides -p CLI arg
alert_groups:
  - endpoint_name: mygroup  # URL path segment for the webhook
    invite_link: "https://simplex.chat/contact#/..."
    group_name: "Optional display name override"
deadmans_switch:
  username:
    group: groupname
    alert_threshold_seconds: 3600
    trigger_threshold_seconds: 86400
    alert_message: "User has been inactive"
    inheritance_filepath: /path/to/file
    inheritance_message: "Here is the inheritance document"
```

### Dead man's switch

`monitor_channels` watches incoming SimpleX messages and updates `last_seen` timestamps per user (persisted to `/alerterconfig/ddms.pickle`). `deadmans_switch_notifier` polls every second and fires two-stage alerts: first a text warning (`alert_message`) after `alert_threshold_seconds`, then a file upload (`inheritance_filepath`) after `trigger_threshold_seconds`.

### Observability

Uses the custom `observlib` library (from `github.com/ForgottenBeast/observlib`) which wraps OpenTelemetry tracing/metrics. Configure via env vars: `OTEL_SERVER`, `PYROSCOPE_SERVER` (prod), `PYROSCOPE_DEV_SERVER` (debug mode). Prometheus metrics are exposed at `GET /metrics`.

### Adding a new alert source

1. Create a new Pydantic model in `simplex_alerter/webhook/request_models/` with an async `render() -> str` method
2. Add it to `KnownModels` union in `request_models/__init__.py`

### Nix structure

Uses [snowfall-lib](https://github.com/snowfallorg/lib) with namespace `simplex-alerter`. Nix files live under `nix/`:
- `nix/packages/simplex-alerter/` — Python venv built with uv2nix, wraps all executables with `simplex-chat` on PATH
- `nix/packages/docker-image/` — from-scratch Docker image bundling the venv + `simplex-chat` binary
- `nix/shells/dev/` — dev shell
- `nix/uv_setup.nix` — shared uv2nix workspace setup used by both package and shell
