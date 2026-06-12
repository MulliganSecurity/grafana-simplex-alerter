# Plan: simplex-alerter homeserver deployment bugfix

**Status:** pending approval
**Type:** Multi-repo bugfix epic
**Slug:** `homeserver-deploy-bugfix`
**Repos:**
- `~/Documents/perso/simplex-alerter` (Python — Issue 4 (open question) only if confirmed)
- `~/Documents/perso/machines_conf` (NixOS — bugs 1, 2, 3)

## Context

Three confirmed defects plus one open question block reliable operation of `simplex-alerter` on the homeserver (pi):

1. `alert-simplex.sh` posts to a non-existent route `/api/alert`. FastAPI routes by URL path == SimpleX group name, so the daemon returns 404 and DR-test alerts silently drop (graceful-failure path is taken every time).
2. Servarr `chat` container (which is the dockerized simplex-alerter inside the servarr compose stack) has no `ports` mapping; port 7898 is unreachable from the host. Note: this is independent of bug 1, which targets the **systemd**-based alerter on `:3334`.
3. The systemd `simplex-alerter` service has no `User`/`Group`/`DynamicUser` — it runs as `root`. DB lives at `/home/rancher/alerterDB` and must stay there.
4. **Issue 4 (open question).** `apiGetGroups` may need a `userId` field in simplex-chat v6.4.11. Must verify against a live socket before any code change.

Roadmap is clean. No open epics. Both repos auto-deploy when pushed (NixOS flake update on pi pulls from origin).

## Work Objectives

- Restore end-to-end alerting from DR-test scripts → systemd alerter → SimpleX `BackupDr` group.
- Make dockerized servarr alerter (port 7898) reachable from host for webhook callers.
- Drop the systemd alerter to a non-root user (with AppArmor confinement in complain mode) without breaking the existing DB path.
- Verify (and only if needed, fix) the `apiGetGroups` call shape.

## Guardrails

### Must have
- All Nix changes pass `statix check` and `deadnix .` on the changed file.
- Python changes (if any) pass `ruff check` and `pyright`.
- Security review on Issue 3 (systemd hardening + AppArmor) before merge — code-reviewer + security-reviewer.
- Post-deploy smoke tests: `curl -X POST http://localhost:3334/BackupDr` and a Sonarr test webhook to `:7898`.
- `User = "rancher"` for the systemd service so `/home/rancher/alerterDB` stays readable/writable without migration.
- `/alerterconfig/` directory created by `systemd.tmpfiles.rules` with `0750 rancher rancher` ownership so the daemon can write `ddms.json` and inheritance files without crashing on first write, and without leaking sensitive inheritance documents to other users on the box (latent landmine — current pi config has no `deadmans_switch` section, so it is dormant, but the directory write path is hardcoded in `chat.py:16` and `webhook/__init__.py:172-179`).
- AppArmor profile attached to the systemd service via the raw `security.apparmor.policies` NixOS attribute in `"complain"` mode (per AGENTS.md AppArmor standing invariant; promotion to `"enforce"` is a follow-up after validation). Note: the methodology helper `mkApparmorProfile` is not defined in this `machines_conf` tree, so we use the raw NixOS attribute directly — see T2 for the profile body.
- TLA+ gate is NOT required for this epic (bugfix, no new invariants, no new state machines). Justification to be recorded in the spec task close note per AGENTS.md spec-dep-validator: changes are configuration-level (route literal, service user, port mapping, optional payload field) and do not introduce or modify any concurrent protocol behaviour that warrants TLC validation.

### Must NOT have
- Bumping `simplex-chat` past v6.4.11.
- Switching to `DynamicUser` (would change DB ownership and force migration).
- Docker workarounds outside the existing Nix-managed compose stack.
- Any `Co-authored-by` or AI-attribution trailers in commits.
- Staging `.omc/plans/` or `.omc/specs/` on the code branch (agentic orphan branch only).
- Pre-deciding the T6 fix shape before T0 evidence is reviewed.

## RALPLAN-DR Summary

### Principles
1. **Two-track parallelism over serial.** Bugs 1+3 (same module, both touch systemd-alerter integration) land together with the AppArmor profile in a single commit; bug 2 (servarr container) runs in a parallel lane.
2. **Verify before code.** Issue 4 starts with an open-ended live-socket probe against a local instance; no speculative Python edits, and no pre-decided fix shape.
3. **Preserve DB continuity.** Keep `/home/rancher/alerterDB` reachable — `User = "rancher"` is non-negotiable.
4. **Security review is gating, not optional.** Issue 3 is a privilege-drop change; code-reviewer (opus) + security-reviewer mandatory before push.
5. **One push per repo when possible.** Auto-deploy means each push triggers a homeserver rebuild; batch related commits before pushing to avoid deploy thrash.

### Decision Drivers (top 3)
1. **Blast radius of `User = "rancher"` change.** rancher is a real human user on pi; sharing the UID with a long-running daemon is acceptable for a homeserver but flagged in security review.
2. **Auto-deploy coupling.** Each `git push` to either repo triggers a homeserver flake update; sequencing commits matters more than usual.
3. **Apparent `/api/alert` route may be evidence of a missing feature, not a script typo.** Possible alternative: implement `/api/alert` with `group_name` body field. Rejected — see options.

### Viable Options

**Option A: Fix the script (`/BackupDr` route).** Change `alert-simplex.sh` to hit `http://localhost:3334/BackupDr`. Body still includes `group_name` field which the route ignores. One-line change, zero new code.
- Pro: minimal blast radius; matches existing FastAPI routing contract.
- Pro: works immediately on homeserver after push.
- Con: caller still embeds `group_name` in body, slight redundancy (cleanup tracked as a follow-up).

**Option B: Add `/api/alert` route to FastAPI app, route by `group_name` body field.** Net-new Python code, schema design, tests.
- Pro: more REST-ful contract; multi-group senders need no URL surgery.
- Con: new code + tests in two repos for the same outcome; longer turnaround; expands surface area against an already-pinned simplex-chat version.
- **Rejected:** scope creep for a bugfix epic. Defer to future API redesign.

**Option C: Wrap systemd service via Nix `users.users.simplex-alerter` (new system user) + migrate DB.** Cleanest privilege isolation.
- Pro: lowest principle-of-least-privilege risk.
- Con: forces DB migration (`/home/rancher/alerterDB` → `/var/lib/simplex-alerter/`), schema continuity risk on first start, requires one-shot migration unit.
- **Rejected for this epic:** out of scope for a bugfix; tracked separately. `User = "rancher"` is the bounded fix; new-user migration is its own epic.

**Selected:** Option A for bug 1; keep Option C as a follow-up backlog item; in-place `User = "rancher"` + AppArmor complain profile + `/alerterconfig` tmpfiles entry for bug 3.

## Critical Path & Parallel Lanes

```
Lane M (machines_conf — sequential):
  T1 (verify) ─→ T2 (bug 1+3 combined + AppArmor + tmpfiles) ─→ T3 (bug 2 servarr)
                          │                       │
                          └──────► T4 (security review of bug 3) ──┐
                                                                   ▼
                                                          T5 (push & deploy)

Lane S (simplex-alerter — parallel from T0, against LOCAL instance only):
  T0 (probe apiGetGroups via local socket) ─→ [conditional T6: fix client.py — shape TBD post-T0]
                                                                   │
                                                                   ▼
                                                          T7 (push if T6 ran)

Lane V (verification — gated by T5 & T7):
  T8 (smoke test on homeserver)
```

**Critical path:** T0/T1 → T2 → T4 → T5 → T8 (machines_conf side dominates because deploy lives there).
**Parallel work:** T0 (lane S) runs concurrent with T1 against a LOCAL simplex-chat instance (NOT the live pi service — eliminates the race where Lane M T2 deploy invalidates T0 results); T3 can interleave with T2 review window.

## Task Flow

### T0 — Probe Issue 4: capture raw `apiGetGroups` response shape
**Repo:** `simplex-alerter` (no commit yet)
**Environment (serialization-critical):**
- Run against a **LOCAL** simplex-chat instance only. Do **NOT** probe the live pi service.
- Spawn the local instance in the dev shell: `nix run .#simplex-chat -- -p 17897 -d /tmp/probe-db` (chosen port avoids collision with the host's 7897 default).

**Tooling note (C1 — corrected):**
The wire format is `{"corrId":"1","cmd":"/groups"}` (see `transport.py:203` and `command.py:494`). Either (a) wscat: send `{"corrId":"1","cmd":"/groups"}` and read one message, OR (b) instantiate ChatClient harness. Both work. The question to answer is: what does the server respond with when we send `/groups` and there may be no active user context? The likely real symptom is a `chatCmdError` with `errorType.type == 'noActiveUser'`, which would mean the real fix is calling `/u` (showActiveUser) before `/groups` — exactly candidate pattern (b) in T6. Additional note: the `/tmp/probe-db` probe may need an active user to return a meaningful response; run `createActiveUser` first with a throwaway profile, document the full call sequence.

**Steps:**
1. Start the local simplex-chat instance as above.
2. Probe via either (a) wscat sending `{"corrId":"1","cmd":"/groups"}` and reading one message, or (b) `ChatClient` pointed at `ws://127.0.0.1:17897`.
3. If the server responds with `chatCmdError` / `noActiveUser`, run `createActiveUser` with a throwaway profile, then retry `/groups`. Document the full call sequence (active-user setup → `/groups`) in the KB note.
4. Issue `apiGetGroups` (the same call site exercised at `webhook/__init__.py:278-280`).
5. Capture the **raw response payload verbatim** — full JSON, including `type` field, any error body, any user-id-related field names.
6. **Repeated-call validation (M4):** invoke `apiGetGroups` in a loop (≥60 iterations, ~1/sec) and confirm no errors recur — this mirrors the `deadmans_switch_notifier` hot loop at `chat.py:50-54`. Capture any drift, throttling, or state-dependent failure.
7. Post the raw payload + the loop result to KB at path `debugging/simplex-chat` via `kb_add` with `kind="observation"` and an excerpt evidence row referencing `simplex_alerter/simpx/client.py:265-270`.

**Acceptance:**
- Raw `/groups` (i.e. `apiGetGroups`) response payload captured and posted to KB at `debugging/simplex-chat`.
- **M4:** Validate that `apiGetGroups` can be called repeatedly without errors — the `deadmans_switch_notifier` hot loop at `chat.py:50-54` calls `api_get_groups()` every second. A single successful call is **not** sufficient evidence; the loop test in step 6 is required.
- The KB entry is the deliverable. T6 content is defined inline in the spec close note **after** T0 evidence is reviewed (not pre-decided here).
- T0 must NOT pre-specify the fix; open-ended investigation only.

### T1 — Verify bugs 1, 2, 3 against HEAD of `machines_conf`
**Repo:** `machines_conf` (no commit)
**Steps:**
1. Confirm `modules/nixos/simplex-alerter/default.nix:71-74` still has only `Restart`/`RestartSec` and no `User`/`Group`/`DynamicUser`.
2. Confirm `modules/nixos/servarr/default.nix:174-181` `chat` block still lacks `ports`.
3. Confirm `scripts/restore-test/alert-simplex.sh:18` still says `/api/alert`.
4. Grep for `SIMPLEX_ALERTER_URL` (and any other env-var override patterns) across all callers of `alert-simplex.sh`. Confirm no caller overrides the URL such that the route-fix would be bypassed or rendered moot. If any caller overrides, document and adjust T2 accordingly.
5. Identify the servarr-side `endpoint_name` from `machines_conf/systems/x86_64-linux/pi/services.nix` under `servarr.simpleXAlerterConfig.alert_groups`. Record the endpoint name for use in T8 step 4 smoke test URL (`http://127.0.0.1:7898/<endpoint>`).
6. **(M1 — group existence verification)** Confirm `users.groups.rancher` does NOT already exist anywhere in `machines_conf` (grep for `groups.rancher` and `groups."rancher"`). The plan's group declaration in T2 must not conflict with an existing declaration. If found, reconcile in T2.
7. **(M1 — group source-of-truth verification, all three sites)** Confirm rancher's user declaration sites — `machines_conf/systems/seedbox.nix`, `machines_conf/systems/x86_64-linux/basicServer/default.nix`, and `machines_conf/systems/x86_64-linux/darkfront/default.nix` — all set `isNormalUser = true` with **no `group = ...` override** at any site. NixOS defaults `isNormalUser` primary group to `users` (GID 100), and no `users.groups.rancher` is declared anywhere. This is the root cause of the systemd-tmpfiles boot failure that T2 fixes (the previous `0750 rancher rancher` tmpfiles rule resolves to a nonexistent group). If any of the three sites sets a `group = ...` value, the T2 `lib.mkForce` strategy must be reviewed against that site's declaration order before commit. **Note:** neither `basicServer/default.nix` nor `darkfront/default.nix` is imported by pi (pi imports only `seedbox.nix` via `pi/default.nix:24`); checking these peer hosts is purely a defensive confirmation that no peer `group = ...` assignment conflicts with the `lib.mkForce` override should pi ever inherit one of these systems in the future.

**Acceptance:** All three bugs confirmed; env-override grep returns no callers (or callers documented); servarr endpoint name recorded for T8 step 4; `users.groups.rancher` confirmed absent in current tree (so T2's group declaration is additive, not conflicting); rancher's current primary group confirmed as `users` at all three declaration sites (`seedbox.nix`, `systems/x86_64-linux/basicServer/default.nix`, `systems/x86_64-linux/darkfront/default.nix`) — NixOS default for `isNormalUser`; if any drifted, update the spec task and adjust T2/T3 accordingly.

### T2 — Fix bugs 1 & 3 + AppArmor + tmpfiles (single commit)
**Repo:** `machines_conf`

**Three concerns in one commit — justification:**
Bundling bug1 (route fix) + bug3 (User/Group + tmpfiles) + AppArmor profile into a single commit is deliberate, and consistent with the minimum-blast-radius principle:
- Avoids an extra deploy cycle (auto-deploy fires on every push; sequencing related changes minimizes deploy thrash).
- AppArmor profile is in `"complain"` mode and so cannot break the service even on a misconfiguration — it logs DENIED lines to `dmesg`/audit but does not enforce.
- The `/alerterconfig` tmpfiles entry is a strict prerequisite of the `User = "rancher"` change (without it the daemon would crash on first write to `/alerterconfig/ddms.json` if `deadmans_switch` is ever enabled), so it must land in the same commit.
- All three changes are scoped to the same module (`modules/nixos/simplex-alerter/default.nix`) plus the script; review surface stays bounded.

**Files:**
- `scripts/restore-test/alert-simplex.sh` — change line 18 to `http://localhost:3334/BackupDr` (also update the descriptive comment block lines 2-13 to reflect routing-by-path).
- `modules/nixos/simplex-alerter/default.nix` (or paired commit in the same module — see "Rancher group declaration" note below):
  - **Declare the `rancher` group:** `users.groups.rancher = { };`. The current tree has no `users.groups.rancher` declaration anywhere (verified in T1 step 6), and `seedbox.nix:6-19` declares `users.users.rancher.isNormalUser = true` with no `group` override — meaning the primary group defaults to `users`. Without this declaration the `systemd.tmpfiles.rules` entry below resolves to a nonexistent group and systemd-tmpfiles fails at boot. (M1 blocker fix)
  - **Override rancher's primary group:** `users.users.rancher.group = lib.mkForce "rancher";` — flips the primary group from the default `users` to the newly-declared `rancher`. This is what makes `0750 rancher rancher` resolve correctly. **Consequence:** new files created by the rancher human user will have group `rancher` (not `users`); existing files in `/home/rancher` retain their current group ownership. Acceptable on a single-user homeserver — recorded in ADR Consequences.
  - **Preserve rancher's membership in `users` supplementary group (samba regression fix):** `users.users.rancher.extraGroups = [ "users" ];` (additive — no `mkForce` needed). Without this, flipping the primary group from `users` → `rancher` would remove rancher from the `users` group entirely (the current extraGroups list at `seedbox.nix` is only `[ "networkmanager" "wheel" ]`), which breaks the samba paperless share at `machines_conf/systems/x86_64-linux/pi/services.nix:2205-2207` which has `"force user" = "rancher"; "force group" = "users";`. Samba would fail to set the forced group because rancher would no longer be a member of `users`. Keeping `users` as a supplementary group preserves the samba `force group = "users"` directive without further refactor.
  - **Rancher group declaration placement:** the group + primary-group override land in the simplex-alerter NixOS module as part of this commit. Justification: keeping the group declaration physically co-located with the only consumer of the group (the tmpfiles rule + service `Group =`) means the declaration cannot be dropped or reverted without also reverting the tmpfiles rule that depends on it. Alternative placement in `seedbox.nix` rejected — would split a single logical change across two modules.
  - `serviceConfig` gains `User = "rancher"; Group = "rancher";` plus the following hardening directives (M3):
    ```
    NoNewPrivileges = true;
    PrivateTmp = true;
    ProtectSystem = "strict";
    ProtectHome = "read-only";
    ReadWritePaths = [ "/home/rancher/alerterDB" "/alerterconfig" ];
    RestrictAddressFamilies = [ "AF_UNIX" "AF_INET" "AF_INET6" ];
    ```
    Note: `ProtectHome = "read-only"` + `ReadWritePaths = ["/home/rancher/alerterDB" "/alerterconfig"]` are compatible per `systemd.exec(5)`; the `ReadWritePaths` carve exceptions. Verify in T8.
  - Add `systemd.tmpfiles.rules = [ "d /alerterconfig 0750 rancher rancher -" ];` so the daemon can write `/alerterconfig/ddms.json` (path hardcoded in `chat.py:16`) and inheritance files (`webhook/__init__.py:172-179`) under `User=rancher`. Without this, the daemon crashes on first deadman's-switch write — latent landmine. (M1) **Note:** the inheritance documents and `ddms.json` are sensitive; `0750 rancher rancher` keeps the directory readable only by the `rancher` user/group. Because this commit also declares `users.groups.rancher` and forces rancher's primary group to `rancher` (above), the group component resolves cleanly and no other normal user on the box can list/read the directory. The previous `0755 rancher:users` shape would have been a privacy regression.
  - Attach an AppArmor profile via the raw NixOS `security.apparmor.policies` attribute in `"complain"` mode. **Why not `mkApparmorProfile`:** a tree grep finds `mkApparmorProfile` only in a seeds documentation file (`modules/home/agentic-config/seeds/universal-seeds.nix:59`) — there is no actual Nix function definition in `machines_conf`. The helper appears to come from an external methodology doc that was never implemented here. Use the raw `security.apparmor.policies` shape directly:
    ```nix
    security.apparmor.policies."simplex-alerter" = {
      state = "complain";
      profile = ''
        include <tunables/global>
        # simplex-alerter AppArmor profile (complain mode)
        # Promote to "enforce" after T8 soak validation
        /nix/store/*/bin/simplex-alerter {
          include <abstractions/base>
          # Binary and lib access
          /nix/store/** r,
          /nix/store/**/bin/simplex-chat Pix,
          /nix/store/**/bin/bash ix,
          /nix/store/**/bin/python* ix,
          include <abstractions/python>

          # DB and state directories
          /home/rancher/alerterDB/** rwk,
          /alerterconfig/** rwk,

          # PTY for pexpect
          /dev/pts/* rw,
          /dev/ptmx rw,

          # TLS / DNS
          /etc/ssl/certs/** r,
          /etc/resolv.conf r,
          /etc/hosts r,

          # System pseudo-files
          /dev/null rw,
          /dev/urandom r,
          @{PROC}/self/** r,
          @{PROC}/sys/kernel/random/uuid r,

          # Network
          network inet stream,
          network inet6 stream,

          # Sockets / IPC
          network unix stream,
        }
      '';
    };
    ```
    Coverage rationale per rule: `simplex-chat Pix` is a profile-inheriting exec transition for the child process spawned at runtime (NOT just `r` — pexpect/subprocess invoke it as a child); `/dev/pts/* rw` + `/dev/ptmx rw` for the pexpect PTY (`chat.py:39`); `/etc/ssl/certs/** r` + `/etc/resolv.conf r` + `/etc/hosts r` for OTel outbound TLS; `@{PROC}/sys/kernel/random/uuid r` for Python's `secrets` module. **Note:** first-run DENIED lines are expected; review `journalctl -k | grep apparmor=DENIED | grep simplex-alerter` after T8 and refine the profile before promoting to enforce.

    **Profile header / execve chain (Architect rec):** Profile header `/nix/store/*/bin/simplex-alerter` matches the bash wrapper; the actual confined process is python3.13 via the `.simplex-alerter-wrapped` shebang. The `ix` transitions for `bash` and `python*` ensure the real long-lived process is confined (the kernel enforces AppArmor on the actual `execve`'d binary, not the entrypoint name). `include <abstractions/python>` covers Python's runtime needs (stdlib reads, locale, etc.). Reference: `machines_conf/systems/x86_64-linux/pi/apparmor.nix:31-69` (litellm-sidecar) for the proven pattern — it already handles the python/bash exec chain correctly and is the canonical template for `wrapProgram`-wrapped Python services on this host.

**Acceptance:**
- `statix check modules/nixos/simplex-alerter/default.nix` clean.
- `deadnix modules/nixos/simplex-alerter/default.nix` clean.
- Shellcheck (if available) clean on `alert-simplex.sh`.
- Profile validation (C2): no DENIED lines from paths the profile reasonably covers after one allow-rule revision pass; first-run DENIED lines from PTY, child exec (simplex-chat), and TLS paths are expected and acceptable for landing complain-mode — document them and fix in the revision pass. Recorded in the spec close note.
- **tmpfiles ordering (Architect rec):** confirm `systemd-tmpfiles-setup.service` runs before `multi-user.target`, which is correct for `wantedBy = [ "multi-user.target" ]` on the simplex-alerter service — `/alerterconfig` will exist before the daemon starts. No special `After=` on the service unit is required.
- **Group declaration is additive (M1):** `users.groups.rancher` is newly declared by this commit and does not collide with any prior declaration in `machines_conf` (verified in T1 step 6).
- **AppArmor profile compiles without error:** verify during T4 review via `nixos-rebuild dry-run` (or equivalent — `nixos-rebuild build` against the pi config) that the raw `security.apparmor.policies."simplex-alerter"` block evaluates and the profile compiles. Compile failure must be fixed before push to T5.
- Commit subject: `fix(simplex-alerter): correct alert route, drop service privileges, add AppArmor profile`
- Commit trailers:
  - `Constraint: DB path /home/rancher/alerterDB must remain readable`
  - `Constraint: AppArmor stays in complain mode until validated under real workload (per AGENTS.md AppArmor invariant)`
  - `Rejected: DynamicUser | forces DB migration`
  - `Rejected: split into three commits | three deploy cycles for one logical change; complain-mode profile is non-enforcing so coupling is safe`
  - `Confidence: high`
  - `Scope-risk: narrow`
  - `Directive: simplex-alerter daemon writes to /alerterconfig/ when deadmans_switch config is set. If you enable deadmans_switch on this service while running as User=rancher, also confirm the systemd.tmpfiles entry is still present or extend ReadWritePaths. The current pi config has no deadmans_switch section so the path is dormant, but removing the tmpfiles entry without that audit will re-introduce a crash on first dead-man-switch write.` (M3)
  - `Directive: this commit declares users.groups.rancher and forces rancher's primary group to "rancher". The systemd.tmpfiles rule "d /alerterconfig 0750 rancher rancher -" depends on that group existing. Do not delete the group declaration or the lib.mkForce override without also reverting the tmpfiles rule and serviceConfig.Group, otherwise systemd-tmpfiles-setup.service will fail at boot.` (M1)
  - `Directive: rancher's extraGroups includes "users" explicitly (not via isNormalUser default) to preserve samba force group = "users" at pi/services.nix:2207. Do not remove this without auditing samba share permissions.`
  - `Directive: rancher primary-group override and /alerterconfig ownership are inside mkIf cfg.enable. Disabling services.simplex-alerter on pi will silently revert rancher's primary group from rancher back to the default users and break /alerterconfig ownership. Coordinate any service-disable with a tmpfiles/group audit.`

### T3 — Fix bug 2 (servarr chat container ports)
**Repo:** `machines_conf`
**File:** `modules/nixos/servarr/default.nix` — `chat` service block (lines 174-181) gains `ports = [ "127.0.0.1:7898:7898" ];`.
**Acceptance:**
- `statix check` clean on the file.
- `deadnix` clean.
- Commit subject: `fix(servarr): expose simplex-alerter container on 127.0.0.1:7898`
- Confirms loopback-only binding (not `0.0.0.0:7898:7898`) — Tor/loopback hygiene.

### T4 — Security review of T2 (privilege drop + AppArmor + tmpfiles)
**Repo:** `machines_conf` (no new commit; review only)
**Agents:** `oh-my-claudecode:code-reviewer` (opus) and `oh-my-claudecode:security-reviewer`.
**Inputs:** `git diff` of T2 commit; explicit instruction to flag any path where:
- A daemon running as `rancher` (a real user) could enable lateral movement.
- DB file mode/ownership assumptions break.
- AppArmor profile allow rules are over-broad (e.g. `/home/rancher/**` instead of `/home/rancher/alerterDB*`) or under-broad (would cause runtime DENIED noise after promotion to enforce).
- `/alerterconfig` permissions (`0750 rancher rancher`) leak files to other users on the box.
- **(M1)** The `users.groups.rancher = { }` declaration + `users.users.rancher.group = lib.mkForce "rancher"` override: confirm no other module depends on rancher's primary group being `users` (grep `machines_conf` for `group = "users"` lines and for any file-ownership tmpfiles that assume rancher's group is `users`). Confirm `lib.mkForce` is justified (the seedbox module sets `isNormalUser` which implicitly defaults the primary group to `users` — without `mkForce`, the declaration would either no-op or conflict).
- **AppArmor profile syntax check:** extract the `profile = ''...''` string from T2, write to `/tmp/simplex-alerter.apparmor`, run `apparmor_parser -Q /tmp/simplex-alerter.apparmor`. This fast syntax check is independent of NixOS evaluation and should be run before relying on `nixos-rebuild dry-run`. Confirm the profile parses without error — parse failures abort the deploy. In particular, confirm `include <tunables/global>` precedes any `@{...}` macro usage.

**Additional inputs (M3):**
- Explicitly verify the AppArmor allow-list as if it were a standalone commit (per Architect recommendation) — review every allow rule for justification.
- Verify `NoNewPrivileges = true` prevents `wheel`/sudo escalation from a compromised process.
- Verify `ReadWritePaths` exceptions (`/home/rancher/alerterDB`, `/alerterconfig`) are the only writable paths and that `ProtectSystem = "strict"` + `ProtectHome = "read-only"` are compatible with those carve-outs at runtime.
- **AppArmor profile header / execve chain check (Architect rec):** Verify the AppArmor profile header binary path (or glob pattern) matches the actual long-lived process after the `wrapProgram` bash→shebang python execve chain. Use the litellm-sidecar profile at `apparmor.nix:31-69` as the proven template. Flag any first-run DENIED line whose path is NOT in {`python*`, `bash`, `simplex-chat`, `.simplex-alerter-wrapped`} as a real allow-list gap (not expected noise). Confirm enforce-mode promotion is blocked for this epic — complain only until the soak window in the follow-up.

**Acceptance:** Zero Critical findings. Important findings either addressed or explicitly accepted with rationale appended to commit body (do NOT amend — new fixup commit if needed). AppArmor header/execve chain verification (above) explicitly recorded in the review note; any DENIED-line path outside {`python*`, `bash`, `simplex-chat`, `.simplex-alerter-wrapped`} treated as an allow-list gap, not expected noise; enforce-mode promotion confirmed blocked for this epic (complain only).

### T5 — Push `machines_conf`
**Steps:** `git push` after T2 + T3 + T4 all pass. Single push (both commits at once) to avoid double-deploy.
**Rollback plan:** If T8 step 1 shows the service failed to start after deploy, run `git revert <T2-sha> && git push` to trigger auto-rollback. Confirm the previous-state DB is intact at `/home/rancher/alerterDB` (mode/ownership preserved, no WAL corruption) before re-attempting any fix.
**Acceptance:**
- Push succeeds.
- Homeserver picks up the change within the normal deploy window (~few min).

### T6 — Conditional: fix `apiGetGroups` payload (shape TBD)
**Repo:** `simplex-alerter`
**Prerequisite:** T0 evidence reviewed and a fix is determined to be needed.
**Content TBD — defined inline in the spec close note after T0 evidence is reviewed.** Two candidate patterns to evaluate (selection deferred to post-T0):
- **(a)** Cache `active_user_id` on `ChatClient`: query once via `api_get_active_user()` during connect/startup, store as an instance attribute, reuse on every subsequent call site including the reconnect/groups path at `webhook/__init__.py:278-280`. Lower latency, one extra startup roundtrip.
- **(b)** Per-call `showActiveUser` before each `apiGetGroups` invocation. Simpler patch (no `ChatClient` state change), at the cost of one extra roundtrip per call.

Select **(a)** or **(b)** based on T0 findings (and based on whether T0 shows that `userId` is even the field name the server expects — T0 may surface a different fix entirely, e.g. a wholly different payload key or a server-side change request).

**File:** `simplex-alerter/simplex_alerter/simpx/client.py:265-270` (likely target; confirm against T0 evidence).

**Acceptance:**
- New unit test in `tests/` exercising the `api_get_groups` payload shape (mock the socket; assert the payload matches the shape T0 determined). The test assertion is written from scratch based on T0 evidence. Do NOT re-use any prior userId-centric assertion templates — the T0 wire-level probe may show the fix is unrelated to userId (e.g., `noActiveUser` error requiring `showActiveUser` → then `apiGetGroups`, not a payload field change).
- `ruff check` clean.
- `pyright simplex-alerter/` clean.
- Commit subject: `fix(simpx/client): align apiGetGroups payload with simplex-chat v6.4.11`
- Trailers (template; finalize once T0 verdict is in): `Constraint: simplex-chat v6.4.11 payload shape per T0 evidence`, `Confidence: high` (based on T0 raw response).

### T7 — Conditional: push `simplex-alerter`
**Prerequisite:** T6 ran.
**Steps:** Push to remote so the homeserver flake update picks up the new derivation hash.

### T8 — Post-deploy smoke verification
**Where:** homeserver (pi), after T5 (and T7 if applicable) deploy lands.
**Steps:**
1. `systemctl status simplex-alerter` — confirm `User=rancher`, active, no recent restarts.
2. `ps -o user= -p $(pidof simplex-alerter)` — confirm not `root`.
3. `curl -X POST http://localhost:3334/BackupDr -H 'Content-Type: application/json' -d '{"group_name":"BackupDr","title":"smoke","description":"plan T8","severity":"info"}'` — confirm **HTTP 200** (locked — not "or whatever the success code is") and the message arrives in the SimpleX `BackupDr` group. Confirm the `BackupDr` group is already joined by the daemon on startup (per `modules/nixos/simplex-alerter/services.nix:1339-1341`); no manual invite-link step needed.
4. From host: `curl -X POST http://127.0.0.1:7898/<servarr-endpoint> ...` with a Sonarr-shaped payload — confirm the servarr-side container is reachable on 7898.
5. (If T6 ran) tail the journal of `simplex-alerter` after start, confirm no `apiGetGroups` errors and groups list populates.
5b. **(M4)** Run the daemon for >60 seconds after deploy. Tail the journal. Confirm no recurring `apiGetGroups` errors in the log. If errors appear even without T6 having run, T0 evidence missed something and T6 must be reopened. (This mirrors the `deadmans_switch_notifier` hot loop at `chat.py:50-54` which calls `api_get_groups()` every second in production.)
6. Verify `/home/rancher/alerterDB` files have `rancher:rancher` ownership and the daemon can still read/write them. **DB ownership migration:** if DB files show `root:root` ownership (the daemon previously ran as root) OR `rancher:users` ownership (pre-existing files predating this commit's primary-group change), run `chown -R rancher:rancher /home/rancher/alerterDB` once on pi before attempting the next start. Consider adding an idempotent `ExecStartPre = "+${pkgs.coreutils}/bin/chown -R rancher:rancher /home/rancher/alerterDB"` to `serviceConfig` if the chown is needed (the `+` prefix means the `ExecStartPre` runs as root even when `User=rancher`, which is appropriate here).
7. `aa-status | grep simplex-alerter` — confirm AppArmor profile is loaded in complain mode. (M2)
8. `journalctl -k | grep apparmor | grep simplex-alerter` — first-run DENIED lines are expected (PTY, child exec for `simplex-chat`, TLS paths). The gate (C2) is: **no DENIED lines after one allow-rule revision pass**, not zero on first probe. Document first-run DENIED lines, extend the allow-list, redeploy, and re-check.
9. `ls -la /alerterconfig/` — confirm directory exists with mode `0750` and `rancher:rancher` ownership (created via `systemd.tmpfiles.rules`) after first run. (M1) Also confirm writability: `sudo -u rancher touch /alerterconfig/.probe && sudo -u rancher rm /alerterconfig/.probe` should succeed (Architect rec — confirms the directory's group/mode actually let the daemon write, not just that it exists).
10. **Regression check:** existing Grafana/Sonarr webhooks continue to land in their configured SimpleX groups after the deploy. Verify by tailing the daemon journal during a real or replayed webhook event from each integration, or by sending a benign test payload to the existing endpoint paths and confirming delivery. (M2)
11. **/metrics regression:** `curl http://localhost:3334/metrics` returns HTTP 200 with `text/plain` Prometheus exposition (no regression on the metrics endpoint after the privilege drop).
12. **Samba regression probe (paperless share):** from a samba client, write a small test file to the paperless share (the share configured with `"force user" = "rancher"; "force group" = "users";` at `pi/services.nix:2205-2207`). Confirm the file lands on disk with `rancher:users` group ownership (samba forced group still resolves correctly with rancher now having `users` as a supplementary group via `extraGroups`). Then confirm the paperless consumer service can read the file. If group ownership shows as `rancher:rancher` or the samba write fails, the `extraGroups = [ "users" ]` line was either not applied or rancher's group membership did not update — investigate before closing the spec.

**Acceptance:** All 12 checks (1-5, 5b, 6-12) pass. Record outputs in the spec task close note.

## Success Criteria
- DR-test alert script delivers a message to the `BackupDr` SimpleX group end-to-end.
- Servarr container alerter reachable from host at `127.0.0.1:7898`.
- Systemd `simplex-alerter` runs AppArmor-confined as non-root user `rancher` with `NoNewPrivileges = true` preventing sudo escalation; AppArmor profile loaded in complain mode with no DENIED lines (after one allow-rule revision pass) under smoke load, `/alerterconfig` exists with correct ownership (`0750 rancher rancher`), DB at `/home/rancher/alerterDB` still readable/writable. **Note:** `rancher` is in `wheel` — full isolation is tracked as Option C follow-up.
- `apiGetGroups` either confirmed-working as-is or fixed with a regression test, based on T0 evidence (not pre-decided).
- Code-reviewer and security-reviewer both signed off on T2 with zero Critical findings.
- Both repos pushed; homeserver deploy lands cleanly; T8 smoke tests all green; existing Grafana/Sonarr webhook paths continue to work (no regression).

## ADR

- **Decision:** Fix the four issues with the minimum-blast-radius change in each case: route correction in shell, in-place `User = "rancher"` + AppArmor complain-mode profile + `/alerterconfig` tmpfiles entry for systemd, loopback ports binding for servarr container, evidence-then-conditional-fix for `apiGetGroups`.
- **Drivers:** Blast radius of privilege change; auto-deploy coupling on every push; preserve existing DB path without migration; AGENTS.md AppArmor + secrets-storage + workflow-phases invariants.
- **Alternatives considered:**
  - Add `/api/alert` route in FastAPI (rejected — scope creep).
  - Create dedicated system user with DB migration / DynamicUser + DB migration (rejected for this epic — out of scope; backlog as follow-up). **Strongest counterargument:** a one-shot `ExecStartPre` with `cp -nu /home/rancher/alerterDB /var/lib/simplex-alerter/` would be bounded and reversible. Rejected because: (a) `cp -nu` does not migrate a live SQLite WAL correctly; (b) the rollback story on first-start failure is worse; (c) `DynamicUser` removes the ability to manually inspect the DB directory as the `rancher` user for debugging. `NoNewPrivileges = true` achieves the most important security gain (no sudo escalation) without the migration risk.
  - Bind container to `0.0.0.0:7898` (rejected — loopback-only is the homeserver convention).
  - Promote AppArmor profile to `"enforce"` in this epic (rejected — AGENTS.md invariant requires complain → validate → enforce; promotion is a follow-up after T8 + a soak window).
  - Split bug1 / bug3 / AppArmor into three separate commits (rejected — three auto-deploy cycles for one logical change; complain-mode profile cannot break runtime; review surface stays bounded by single module).
  - Pre-decide T6 fix shape (cache vs per-call) at plan time (rejected — would commit to a fix before evidence; T0 may show userId isn't the right field at all).
- **Why chosen:** Each option matches the "fix the bug, not the architecture" rubric for a bugfix epic. Architectural improvements (dedicated user, REST-ful body-routed API, AppArmor enforce) are tracked as follow-ups, not bundled here.
- **Consequences:**
  - `simplex-alerter` shares UID with a real user (`rancher`) — accepted risk on a homeserver; recorded in security-review acceptance note.
  - **(M1 — primary group change)** Changed rancher's primary group from `users` to `rancher`; `users` retained as explicit supplementary group (see `extraGroups = [ "users" ]` in T2) to preserve the samba paperless share's `force group = "users"` at `pi/services.nix:2207`. rancher remains a member of `users` supplementary. New files created by the rancher human user after deploy will have primary group `rancher` instead of `users` (but rancher can still read/write `users`-group files because of the supplementary membership). Existing files in `/home/rancher` retain their current `users` group ownership until manually re-chowned. Acceptable on a single-user homeserver. If a future tenant joins the box, audit `/home/rancher` group ownership and shared-group workflows before granting any access.
  - **(M2)** `rancher` is in `wheel` (per `seedbox.nix:6-19` `extraGroups = [ "networkmanager" "wheel" ]`), so running the daemon as rancher is **not** a strong privilege drop — a compromised process could attempt sudo escalation. The primary security value is AppArmor confinement plus `NoNewPrivileges = true` (which closes the sudo pivot path from this process). Full privilege isolation requires Option C (dedicated system user, backlogged).
  - `alert-simplex.sh` callers still send `group_name` in the body even though the FastAPI route ignores it — minor redundancy, acceptable; cleanup tracked as a follow-up.
  - AppArmor profile remains in complain mode until a follow-up soak/promote epic; some attack surface remains until promotion.
  - `/alerterconfig` is created proactively even though current pi config has no `deadmans_switch` section — pre-empts a future crash; cost is a single empty directory on disk.
- **Follow-ups (not in this epic):**
  - Create `users.users.simplex-alerter` system user with DB migration (Option C).
  - Optionally add `/api/alert` route with body-based group routing (Option B).
  - Document the route-by-path convention in `simplex-alerter` README so future callers don't repeat bug 1.
  - Promote the AppArmor profile from `"complain"` to `"enforce"` after a soak window (collect dmesg for ≥1 week with no DENIED lines under real workload, then flip).
  - **Minor cleanup:** remove the `group_name` field from the `alert-simplex.sh` POST body — currently redundant since the route ignores it; eliminates ambiguity for future contract readers.

## Open Questions
- T0 evidence may surface specific questions about the `userId` source on `ChatClient` (cache vs per-call, or a different field name entirely). The T6 trailer template, file target, and the fix shape itself are deliberately deferred to the spec close note once T0 evidence is in. Address inline when T6 runs.
