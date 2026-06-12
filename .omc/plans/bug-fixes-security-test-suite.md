# Plan: Bug Fixes, Security Hardening & Test Suite

**Status:** Approved
**Source:** ralplan consensus (Planner → Architect → Critic)
**Date:** 2026-04-30

---

## Decision

Address all findings from the ralplan code review of `simplex-alerter`: fix critical and high bugs, harden security, and establish a full test suite with CI pipeline.

## Decision Drivers

1. The app has unauthenticated external webhook input and a pickle RCE vector — security hardening is non-negotiable
2. Sonarr alert rendering is silently broken in production (H2 template unpack bug)
3. No tests exist today; CI pipeline mirrors dev shell toolchain exactly

## Alternatives Considered

- **Fix only security issues, defer tests** — rejected: tests are required to prevent regressions when fixing security issues
- **Full gitflow branching** — rejected: project is small, trunk-based is sufficient
- **tox for test runner** — rejected: fights the Nix/uv venv machinery; pytest via `uv run` is idiomatic

## Consequences

- All webhook callers must be updated to send `Authorization: Bearer <token>` after H1 is implemented
- Pickle state file at `/alerterconfig/ddms.pickle` must be migrated to JSON on first startup after C2 fix
- Coverage gate starts at 60%, ratchets to 80% in a follow-up PR

## Follow-ups

- Document the webhook authentication scheme in README
- Consider adding a migration script for existing pickle state files

---

## Findings Summary

| Severity | ID | Description | File |
|---|---|---|---|
| Critical | C1 | Dual simplex-chat process / pexpect leak | `chat.py:36`, `webhook/__init__.py:175` |
| Critical | C2 | Pickle RCE deserialization | `webhook/__init__.py:90`, `chat.py:122` |
| High | H1 | No webhook authentication | `webhook/__init__.py:249` |
| High | H2 | Sonarr template vars missing `**` unpack | `servarr.py:54` |
| High | H3 | Hardcoded port 7897 in pexpect | `chat.py:36` |
| Medium | M1 | `attribute=` typo drops metric | `webhook/__init__.py:128` |
| Medium | M2 | `logger.warn` deprecated | `chat.py:128` |
| Medium | M3 | New ChatClient per request | `webhook/__init__.py:258` |
| Medium | M4 | Log injection via endpoint/body | `webhook/__init__.py:271,276` |
| Medium | M5 | Dead man's switch timer resets silently | `webhook/__init__.py:113` |
| Low | L1 | `@app.on_event` deprecated | `webhook/__init__.py:159,235` |
| Low | L2 | Module-level mutable globals | `webhook/__init__.py:32-33` |
| Low | L3 | Fragile `host:port` string parsing | `webhook/__init__.py:172` |

---

## Task Flow

### Step 1: Fix one-liner bugs (H2, M1, M2)

- `servarr.py:54` — add `**` to `render_async(self.model_dump())` → `render_async(**self.model_dump())`
- `webhook/__init__.py:128` — fix `attribute=attrs` → `attributes=attrs`
- `chat.py:128` — fix `logger.warn` → `logger.warning`

Branch: `fix/one-liner-bugs`

### Step 2: Fix C1 — pexpect leak and H3 — hardcoded port

- `chat.py` — call `chat.terminate()` after `expect("Current user: .*")` in `init_chat()`
- `chat.py` — add `port` parameter to `init_chat()`, remove hardcoded `7897`
- `__main__.py` — pass parsed port from `-e` argument to `init_chat()`

Branch: `fix/C1-pexpect-and-H3-port`

### Step 3: Fix C2 — replace pickle with JSON

- `webhook/__init__.py` — replace `pickle.loads` with JSON deserialization; handle `datetime` via `isoformat()`/`fromisoformat()`
- `chat.py` — replace `pickle.dumps` with JSON serialization
- Define `LIVENESS_DATA_PATH` constant in one place, import where needed
- Add startup log warning when existing pickle file detected (migration notice)

Branch: `fix/C2-json-state`

### Step 4: Implement H1 — webhook authentication

- `config.py` — add optional `webhook_secret` field to config schema
- `webhook/__init__.py` — add `Authorization: Bearer <token>` check as FastAPI dependency on `POST /{endpoint}`
- Return HTTP 401 when token missing or invalid
- Document in CLAUDE.md config structure

Branch: `feat/H1-webhook-auth`

### Step 5: Fix M3 — shared ChatClient on app.state

- `webhook/__init__.py` — move `ChatClient.create()` call to startup event, store on `app.state.chat_client`
- Add reconnect wrapper: if `client.connected` is False, recreate client
- Remove per-request `ChatClient.create()` call from `post_message()`

Branch: `fix/M3-shared-client`

### Step 6: Fix M4 + M5 — log sanitization and timer reset warning

- `webhook/__init__.py` — truncate body to 500 chars before logging; sanitize `endpoint` to `[a-zA-Z0-9_-]` only
- `webhook/__init__.py:113` — add `logger.warning()` when `last_seen` is initialized to `now()` (timer reset)

Branch: `fix/M4-M5-log-and-timer`

### Step 7: Low-priority cleanup (L1, L2, L3)

- `webhook/__init__.py` — migrate `@app.on_event` to `@asynccontextmanager` lifespan
- `webhook/__init__.py` — move globals to `app.state`
- `webhook/__init__.py` — replace `simplex_endpoint.split(":")` with `urllib.parse.urlparse()`

Branch: `chore/L1-L2-L3-cleanup`

### Step 8: Add pytest dev dependencies and config

- `simplex-alerter/pyproject.toml` — add `[dependency-groups] dev` with pytest, pytest-asyncio, pytest-cov, httpx, time-machine
- Add `[tool.pytest.ini_options]`, `[tool.coverage.run]`, `[tool.coverage.report]` sections
- Verify `uv run pytest` runs with no errors (empty suite)

Branch: `chore/test-deps`

### Step 9: Unit tests

Files to create:
- `tests/conftest.py` — shared fixtures (mock ChatClient, sample payloads)
- `tests/unit/test_request_models_servarr.py` — H2 regression: assert series title in rendered output
- `tests/unit/test_request_models_grafana.py` — title+message concatenation
- `tests/unit/test_request_models_forgejo.py` — all event types for Push, PR, Issue, Workflow, Comment
- `tests/unit/test_config.py` — load/get, missing file, optional bot_name
- `tests/unit/test_chat_get_groups.py` — populated list, empty list, malformed entry skipped

Branch: `test/unit-suite`

### Step 10: Integration tests

Files to create:
- `tests/integration/test_webhook_routing.py` — TestClient + mocked ChatClient: known group 200, unknown group 404, raw JSON fallback, /metrics 200
- `tests/integration/test_deadmans_switch.py` — timer fires after threshold (time-machine), file sent after trigger threshold, reset on user activity, flags prevent duplicates

Branch: `test/integration-suite`

### Step 11: CI pipeline

File to create: `.github/workflows/ci.yml`

Jobs (parallel):
- `lint`: ruff + statix + deadnix
- `typecheck`: pyright
- `security`: bandit + vulnix
- `test`: pytest --cov, coverage gate 60%

Sequential gate:
- `build`: nix build (depends on all above)
- `docker-build`: nix build .#docker-image (main branch only)

Caching: nix-community/cache-nix-action, astral-sh/setup-uv

Branch: `chore/ci-pipeline`

### Step 12: E2E skeleton (optional)

Files to create:
- `docker-compose.e2e.yml` — simplex-chat + alerter services
- `tests/e2e/conftest.py` — skip marker when SIMPLEX_TEST_ENDPOINT not set
- `tests/e2e/test_full_alert_flow.py` — POST → assert message in group

Branch: `chore/e2e-skeleton`

---

## Git Workflow

**Model:** Trunk-based, short-lived feature branches, squash merge to main

**Branch naming:** `fix/<id>-<slug>`, `feat/<slug>`, `chore/<slug>`, `test/<slug>`

**PR rules:**
- All merges via PR, squash merge
- CI must pass (lint + typecheck + security + test + build)
- No direct pushes to main
- Delete branches on merge

**Commit convention:** Conventional Commits (`fix:`, `feat:`, `chore:`, `test:`, `docs:`)
