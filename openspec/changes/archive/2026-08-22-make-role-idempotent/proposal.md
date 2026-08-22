# Proposal: Make the role idempotent

## Why

Re-running `tcharl.ansible_securehost` on an already-configured host reports spurious "changed" tasks because several state-changing commands use a blanket `changed_when: false` shortcut (they always run and never report) or unconditionally restart services. This hides real drift, pollutes CI signals, and blocks enabling molecule's `idempotence` action — which is currently commented out in all three scenarios (`default`, `kvm`, `parallels`).

## What Changes

- Audit every task in the role; classify each `changed_when: false` as either genuinely read-only (kept) or a shortcut on a state-changing command (fixed).
- Replace shortcut `changed_when: false` with exact change detection or conditional guards on non-read-only tasks:
  - `tasks/prereq.yml`: `nmcli general reload` runs only when NetworkManager is not yet using systemd-resolved as its DNS resolver.
  - `tasks/freeipa-client.yml`: the FreeIPA CA certificate is written to `/etc/pki/ca-trust/source/anchors/ipa-ca.pem` only when it differs from what would be fetched; `update-ca-trust` runs only when that anchor actually changed; `systemd-resolved` is restarted only when the `head.conf` template was modified.
  - `tasks/freeipa-client-delete.yml`: `ipa-client-install --uninstall` and the `krb5-libs` reinstall run only when an IPA client is actually present, with exact change reporting.
- Keep `changed_when: false` on genuinely read-only commands (`hostname`, CA serial number query) and normalize its casing to lowercase for consistency.
- Enable the molecule `idempotence` action in all three scenario `test_sequence`s (currently commented out).
- Tag the two known non-idempotent dependencies — `freeipa.ansible_freeipa.ipaclient` include (upstream fix pending at https://github.com/freeipa/ansible-freeipa/pull/1432) and `tcharl.etchost_append` include (remove-and-re-add loop when called with `replace: true`) — with the molecule-native tag `molecule-idempotence-notest`, so they are skipped only during the idempotence action, each with a TODO comment pointing at the upstream PR / a separate openspec change for `tcharl.etchost_append`.
- Verify end-to-end: lint plus full molecule cycle (destroy → converge → verify) and the idempotence check on the default scenario.

## Capabilities

### New Capabilities

- `role-idempotence`: re-running the role against an already-configured host performs no state changes and reports zero changed tasks; molecule scenarios exercise this via the `idempotence` action, with known non-idempotent dependencies excluded only during that action.

### Modified Capabilities

(none — this repo has no existing specs)

## Impact

- **Code**: `tasks/prereq.yml`, `tasks/freeipa-client.yml`, `tasks/freeipa-client-delete.yml` (exact `changed_when` / guards); `molecule/{default,kvm,parallels}/molecule.yml` (enable `idempotence` in `test_sequence`).
- **Behavior**: no functional change on first run; re-runs become no-ops instead of silently re-executing reloads/restarts/reinstalls. The delete flow (`reset_ipa`) gains a presence guard so it is safe to invoke repeatedly.
- **Testing**: molecule `idempotence` action becomes part of every scenario's test sequence; two includes are excluded from that action only, via `molecule-idempotence-notest`, until upstream freeipa PR #1432 releases and `tcharl.etchost_append` is fixed in its own repo (separate openspec change per monorepo AGENTS.md rule 4).
- **Out of scope**: fixing `tcharl.etchost_append` itself (cross-role, separate change), the upstream freeipa collection (PR #1432), and other local roles' idempotency (`tcharl.ansible_routing`, `tcharl.ansible_hostname` are already re-run-clean; verified during implementation).
