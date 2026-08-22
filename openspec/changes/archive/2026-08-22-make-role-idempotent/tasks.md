# Tasks: Make the role idempotent

## 1. Audit baseline

- [x] 1.1 Inventory every `changed_when` usage in `tasks/` (8 known) and classify each task as read-only or state-changing; record the classification in a short note for review
- [x] 1.2 Normalize casing of kept read-only `changed_when: False` to lowercase (`facts.yml` hostname commands, CA serial query)

## 2. Fix prereq.yml (design D2)

- [x] 2.1 Add a read-only check task determining whether NetworkManager already uses systemd-resolved as its DNS resolver (e.g. `/etc/resolv.conf` symlink target and/or `nmcli general` output), registered for reuse
- [x] 2.2 Gate the existing `nmcli general reload` command on that check so it runs only when NM is not yet using systemd-resolved; remove its blanket `changed_when: false`

## 3. Fix freeipa-client.yml (design D3, D4)

- [x] 3.1 Change the CA certificate retrieval shell to capture the PEM to stdout instead of writing `/etc/pki/ca-trust/source/anchors/ipa-ca.pem` directly; register the result
- [x] 3.2 Write the anchor file with `ansible.builtin.copy` (`content=...`, correct owner/mode) so identical content reports ok and differing content reports changed
- [x] 3.3 Gate `update-ca-trust` on the copy task having reported changed; remove its blanket `changed_when: false`
- [x] 3.4 Register the `head.conf` template task and change the systemd-resolved restart to run only when that template was modified (`when: ... is changed`); remove its blanket `changed_when: false`

## 4. Fix freeipa-client-delete.yml (design D5)

- [x] 4.1 Add a read-only presence check for an installed IPA client (e.g. `/etc/ipa/default.conf` exists or freeipa-client package present), registered
- [x] 4.2 Gate `ipa-client-install --uninstall` on the presence check and report changed accurately (changed only when an uninstall actually happened; keep `failed_when: false`)
- [x] 4.3 Gate `dnf -y reinstall krb5-libs` on the same presence check; remove its blanket `changed_when: False`

## 5. Molecule idempotence (design D6)

- [x] 5.1 Enable `- idempotence` in `test_sequence` of `molecule/default/molecule.yml`, between `converge` and `side_effect`
- [x] 5.2 Enable `- idempotence` in `test_sequence` of `molecule/kvm/molecule.yml` (replacing the commented line)
- [x] 5.3 Enable `- idempotence` in `test_sequence` of `molecule/parallels/molecule.yml` (replacing the commented line that referenced PR #1432)
- [x] 5.4 Tag the `freeipa.ansible_freeipa.ipaclient` include in `tasks/freeipa-client.yml` with `molecule-idempotence-notest` plus a TODO comment: remove when freeipa/ansible-freeipa PR #1432 is released (check for a fixed collection release first)
- [x] 5.5 Tag the `tcharl.etchost_append` include in `tasks/freeipa-client.yml` with `molecule-idempotence-notest` plus a TODO comment: remove once the tcharl.etchost_append replace-loop fix lands

## 6. Verification (design D7)

- [x] 6.1 Run lint (`tox -e lint`) and fix any findings
- [x] 6.2 Run the full molecule cycle on the parallels scenario per AGENTS.md: destroy → converge-monorepo → verify-monorepo
- [x] 6.3 Run the idempotence check (`molecule test` or `tox -e idempotence-monorepo -- --scenario-name=parallels`) and confirm zero changed tasks from this role's own tasks; iterate on any task it flags (e.g. firewalld re-run behavior in tcharl.ansible_routing → if flagged, file a separate change and tag temporarily per design risk)
- [x] 6.4 Re-run converge + verify after the idempotence pass to confirm no regression

## 7. Cross-role follow-up (AGENTS.md rule 4)

- [x] 7.1 Create an openspec change in `tcharl.etchost_append`'s repo fixing its remove-and-re-add loop when called with `replace: true` (entry removed only when it does not already match the desired "IP hostname" line); reference it from the TODO comment added in task 5.5
