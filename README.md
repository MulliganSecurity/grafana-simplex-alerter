# simplex-alerter

A FastAPI webhook bridge that forwards alerts from external services (Grafana, Sonarr/Servarr, Forgejo) into SimpleX Chat groups. Includes a dead man's switch that fires a two-stage alert when a monitored user goes silent for too long.

## Architecture

At startup the app:

1. Uses `pexpect` to spawn `simplex-chat` once for database initialisation (`chat.py:init_chat`)
2. Spawns `simplex-chat` again as a long-running WebSocket server (port 7897 by default)
3. Connects to that WebSocket as a client (`simpx/client.py:ChatClient`)
4. Starts two background asyncio tasks: `monitor_channels` and `deadmans_switch_notifier`
5. Joins any configured SimpleX groups via their invite links

The FastAPI app listens on port 7898 (default). Each incoming `POST /{endpoint}` is routed to the SimpleX group whose name matches `endpoint`.

### Key modules

| Path | Purpose |
|------|---------|
| `simplex_alerter/webhook/__init__.py` | FastAPI app, lifespan, webhook route, Prometheus metrics endpoint |
| `simplex_alerter/simpx/client.py` | `ChatClient` — async WebSocket client with corr_id request/response tracking |
| `simplex_alerter/simpx/transport.py` | WebSocket transport layer |
| `simplex_alerter/chat.py` | `init_chat`, `monitor_channels`, `deadmans_switch_notifier` |
| `simplex_alerter/config.py` | YAML config loader; global singleton via `get_config()` |
| `simplex_alerter/webhook/request_models/` | Pydantic models per alert source, each with an async `render() -> str` method |

### Supported alert sources

- **Grafana** — `GrafanaAlert`
- **Sonarr/Servarr** — `ServarrAlert`
- **Forgejo** — `ForgeJoAlerts`

Unknown payloads fall back to pretty-printed JSON.

### Dead man's switch

`monitor_channels` watches incoming SimpleX messages and updates `last_seen` timestamps per user, persisted to `/alerterconfig/ddms.json`. `deadmans_switch_notifier` polls every second and fires two-stage alerts:

1. A text warning (`alert_message`) after `alert_threshold_seconds`
2. A file upload (`inheritance_filepath` + `inheritance_message`) after `trigger_threshold_seconds`

The switch resets if the user becomes active again before the trigger fires.

### Observability

Uses `observlib` (wrapping OpenTelemetry). Configure via environment variables:

| Variable | Purpose |
|----------|---------|
| `OTEL_SERVER` | OTLP exporter endpoint |
| `PYROSCOPE_SERVER` | Pyroscope continuous profiling endpoint (production) |
| `PYROSCOPE_DEV_SERVER` | Pyroscope endpoint used in `--debug` mode |

Prometheus metrics are exposed at `GET /metrics`.

## Configuration

Mount a config file at `/alerterconfig/config.yml` (or pass a path with `-c`):

```yaml
bot_name: alertBot          # optional; overrides the -p CLI flag

# Optional: require a Bearer token on all incoming webhooks
webhook_secret: "s3cr3t"

alert_groups:
  - endpoint_name: mygroup  # URL path segment: POST /mygroup
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

## CLI flags

```
simplex-alerter -c config.yml [options]

  -c, --config FILE        Config file (required)
  -b, --bind-addr HOST:PORT  FastAPI bind address (default: 127.0.0.1:7898)
  -e, --endpoint HOST:PORT   simplex-chat WebSocket address (default: 127.0.0.1:7897)
  -p, --profile-name NAME    Bot display name for first-run DB init (default: alertBot)
  -d, --db-path PATH         simplex-chat database directory (default: /alerterconfig/chatDB)
  -D, --debug                Enable debug mode (higher profiling sample rate, dev Pyroscope)
```

## Building

### Nix — standalone package

```
nix build .#simplex-alerter
```

### Nix — Docker image (from-scratch, no base OS)

```
nix build .#docker-image
```

The output is a tarball at `result`. Load it with:

```
docker load < result
```

### Docker — build via container (CI convenience wrapper)

The `Dockerfile` at the repository root runs the Nix build inside a container. It is not a standalone Docker build — the resulting image still comes from Nix.

```
docker build . -t builder
docker run --rm -v $(pwd):/src builder
docker load < simplex-alerter.tar.gz
```

## Running

```
docker run -p 127.0.0.1:7898:7898 \
  -v /my/alerter/data:/alerterconfig \
  --rm simplex-alerter
```

`/alerterconfig` must contain `config.yml`. The app writes `chatDB/` and `ddms.json` there at runtime.

## Development

All development is done inside the Nix dev shell:

```
nix develop
```

The dev shell provides `uv`, `ruff`, `pyright`, `bandit`, `statix`, `deadnix`, and Python 3.13.

```bash
# Run
uv run simplex-alerter -c config.yml

# Lint (Python)
ruff check simplex-alerter/

# Type check
pyright simplex-alerter/

# Security scan
bandit -r simplex-alerter/simplex_alerter/

# Tests
cd simplex-alerter && uv run pytest --cov=simplex_alerter tests/

# Lint (Nix)
statix check
deadnix .
```

CI runs lint, type check, security scan, and tests before attempting the Nix and Docker builds.

## Adding a new alert source

1. Create a Pydantic model in `simplex_alerter/webhook/request_models/` with an async `render() -> str` method.
2. Add it to the `KnownModels` union in `request_models/__init__.py`.

## Tip the dev (XMR)

85DnG7JvsRCT5FJXKkFstm75Pysani2Q1LMftG4sVLkTWEDqnDcHRqiTYEKzSx1FPvYeJkfXqD7uiXhNxgbYWWij1iyt7rd
