# Design: Make the role idempotent

## Context

See proposal.md for motivation. Current state relevant to the approach:

- The role's tasks live in `tasks/prereq.yml`, `tasks/facts.yml`, `tasks/freeipa-client.yml`, `tasks/freeipa-client-delete.yml` (+ `freeipa-reset-client.yml`). Eight tasks use a blanket `changed_when: false`; four of them sit on state-changing commands.
- Molecule 24's `idempotence` action re-runs the converge playbook and fails if any host line shows `changed=[1-9]`. It natively skips tasks tagged `molecule-idempotence-notest`, but only during the idempotence action (verified in molecule 24.12 source: `provisioner/ansible.py` adds that tag to `--skip-tags` when `action == "idempotence"`). Tags on an `include_role` propagate into the included role's tasks.
- Two dependencies are non-idempotent outside this role's control (user-approved strategy: exclude them from the idempotence action only):
  - `freeipa.ansible_freeipa.ipaclient` (collection 1.17.0, latest release): with our `ipaclient_allow_repair: True`, its "Client deployment" block re-runs on every converge; upstream fix is open at https://github.com/freeipa/ansible-freeipa/pull/1432 and not in any release.
  - `tcharl.etchost_append` (local monorepo role, separate git repo): called with `replace: true`, its first task removes the exact `/etc/hosts` line it later re-adds → every run reports changed. Per monorepo AGENTS.md rule 4 this is a separate openspec change in that role's repo.
- Molecule scenarios `default`, `kvm`, `parallels` all converge the same role; their `test_sequence`s currently have `- idempotence` commented out (parallels' comment references PR #1432).

## Goals / Non-Goals

**Goals:**
- Zero changed tasks from this role's own tasks on a re-run against an already-configured host.
- Accurate change reporting: state-changing commands run only when needed and report `changed` exactly when they modify the system; read-only commands stay `changed_when: false`.
- Molecule `idempotence` action enabled in all three scenarios, passing with the two known-bad dependencies excluded from that action only.

**Non-Goals:**
- Fixing `tcharl.etchost_append` (separate change in its own repo) or the upstream freeipa collection (PR #1432).
- Changing first-run behavior: same end state as today; only re-run reporting/execution changes.
- Making the delete flow (`reset_ipa`) part of molecule's idempotence check — it is an explicit user action, not exercised by converge.

## Decisions

### D1: Classify every `changed_when: false` before touching anything
Audit all eight usages and split them into two classes:
- **Read-only** (keep `false`, normalize casing to lowercase): `hostname` commands in `facts.yml` (×2), the CA serial number query shell in `freeipa-client.yml` (`kdestroy`/`kinit`/`ipa cert-find` only reads state; ticket-cache churn is not persistent system state).
- **State-changing** (fix, see D2–D5): `nmcli general reload`, CA certificate retrieval, `update-ca-trust`, systemd-resolved restart, `ipa-client-install --uninstall`, `dnf -y reinstall krb5-libs`.

Rationale: a blanket `false` on read-only commands is the *exact* answer (they never change state); replacing it with an expression adds noise. The shortcut only exists where a command actually mutates the system.
Alternative considered: rewriting every task to module-based equivalents — rejected, too invasive for little gain; guards + exact expressions are sufficient and reviewable.

### D2: Guard `nmcli general reload` on resolver state (`prereq.yml`)
Add a read-only check task (e.g. `stat` on `/etc/resolv.conf` plus/instead parsing `nmcli general` output) that determines whether NetworkManager already uses systemd-resolved as its DNS resolver; run the reload only when it does not. On re-run the guard fails → task skipped → no changed reported.
Alternative considered: keep the command and derive `changed_when` from before/after output — rejected, a "reload" produces no meaningful diffable output; a state check is both more accurate and cheaper (no needless reloads).

### D3: Make CA certificate retrieval compare-before-write (`freeipa-client.yml`)
Capture the FreeIPA CA certificate to stdout instead of writing it directly into `/etc/pki/ca-trust/source/anchors/ipa-ca.pem`, then write with `ansible.builtin.copy` (`content=...`). The copy module is idempotent by nature: identical content → ok, different → changed. Chain the next two tasks on that result via handlers (the idiomatic way to "run only when X changed"; this also satisfies ansible-lint's `no-handler` rule, which rejects an inline `when: X is changed`):
- `update-ca-trust`: a handler in `handlers/main.yml` notified by the anchor copy task, so it runs only when the anchor file was actually written (changed); drop its blanket `changed_when: false` (the handler carries `changed_when: true` since it only runs on an actual change).
- systemd-resolved restart: see D4.

This also makes the flow self-healing: a deleted or drifted anchor is restored on the next run and reported as changed.
Alternative considered: keep the shell write and add an exact `changed_when` comparing hashes — rejected, duplicates what `copy` does natively and keeps a privileged shell doing file I/O for no reason.

### D4: Restart systemd-resolved only when its config changed (`freeipa-client.yml`)
The `head.conf` template task notifies a `systemd-resolved` restart handler (in `handlers/main.yml`), so the restart runs only when that template was actually modified (changed). Re-run with unchanged content → template reports ok → handler not notified → no restart. (Originally specified as an inline `when: <template> is changed`; converted to a handler to satisfy ansible-lint's `no-handler` idiom rule — same observable contract.)

### D5: Guard the delete flow on client presence (`freeipa-client-delete.yml`)
Add a read-only presence check (e.g. `/etc/ipa/default.conf` exists / freeipa-client package installed). Gate `ipa-client-install --uninstall` and `dnf -y reinstall krb5-libs` on it, with exact change reporting for the uninstall (changed only when an uninstall actually happened; keep `failed_when: false` so absence is not a failure). Re-invoking the flow on a clean host reports no changes.

### D6: Enable molecule idempotence with native tag exclusions
- Uncomment/add `- idempotence` in `test_sequence` of all three scenarios (`default`, `kvm`, `parallels`), between `converge` and `side_effect`.
- Tag the two known-bad includes — `freeipa.ansible_freeipa.ipaclient` and `tcharl.etchost_append` in `tasks/freeipa-client.yml` — with `molecule-idempotence-notest`, each with a TODO comment: ipaclient → "remove when freeipa/ansible-freeipa PR #1432 is released"; etchost_append → "remove once tcharl.etchost_append replace-loop fix lands (separate openspec change)".
- Rationale: molecule 24 skips `molecule-idempotence-notest` tasks only during the idempotence action, so converge/verify behavior is untouched and our role's own tasks remain fully checked. This matches the intent already expressed in the parallels scenario comment.
- Alternatives considered: (a) set `ipaclient_allow_repair: False` + drop `replace: true` to avoid exclusions — rejected by user decision (loses auto-repair; stale `/etc/hosts` entries if IDM IP changes); (b) fix both dependencies in this change — rejected (cross-role scope, AGENTS.md rule 4).

### D7: Verification strategy
Run lint (`tox -e lint`) and the full molecule cycle on the default scenario per monorepo AGENTS.md: destroy → converge-monorepo → verify-monorepo, then `molecule test` (which now includes idempotence) or `tox -e idempotence-monorepo -- --scenario-name=default`. The idempotence action's failure output lists exactly which tasks reported changed — use it to catch anything the audit missed (e.g. firewalld re-run behavior in `tcharl.ansible_routing`).

## Risks / Trade-offs

- [Upstream PR #1432 not released] → ipaclient exclusion stays until a release containing it ships; TODO comment + this design doc track removal. Mitigation: re-check the collection version at implementation time and drop the tag if a fixed release is available.
- [`tcharl.etchost_append` fix lands in another repo/change] → its exclusion persists here until that change is applied; tracked by TODO comment.
- [`tcharl.ansible_routing` firewalld tasks report changed on re-run] (not observed, unverified) → if the idempotence run flags them, it is a cross-role issue: file a separate change and tag temporarily rather than editing that role here.
- [Resolver-state check in D2 may be distribution-specific] → keep the check simple and observable (`/etc/resolv.conf` symlink target / `nmcli general` output); verify on Fedora 44 cloud during implementation; fall back to an always-run reload with exact `changed_when` only if no reliable state signal exists.
- [Chaining `update-ca-trust`/restart on the copy task's changed state] → a manually deleted anchor is restored next run (intended self-healing); no risk of skipping needed work because the copy task re-evaluates content every run.

## Migration Plan

No data or state migration: first-run end state is unchanged; only re-run behavior changes. Rollback = revert the commit (task files + molecule configs are independent and trivially reversible). No version bump required beyond the normal release process.

## Open Questions

None blocking — the exact D2 check mechanism (`stat` on `/etc/resolv.conf` vs `nmcli general` parsing) is finalized during implementation based on what Fedora 44 cloud actually reports; both satisfy the spec's observable contract (reload skipped when already using systemd-resolved).
