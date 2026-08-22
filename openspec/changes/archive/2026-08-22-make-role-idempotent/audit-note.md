# changed_when Audit Note (task 1.1)

Fresh inventory of every `changed_when` usage under `tasks/` — **9 total** (design.md said "8"; count corrected, classification approach unchanged).

| File:Line | Task | Command/module | Classification | Action taken |
|---|---|---|---|---|
| `prereq.yml:50` | Prereq \| reload NetworkManager to have it rely on systemd-resolved | `command: nmcli general reload` | **STATE-CHANGING** (shortcut) | Guarded on resolver state; blanket `false` removed — task runs only when NM is not yet using systemd-resolved, so first-run reports changed accurately and re-runs skip it (tasks 2.1–2.2) |
| `facts.yml:21` | Facts \| retrieve current hostname | `command: hostname` | **READ-ONLY** | Keep `changed_when: false`; casing normalized to lowercase (task 1.2) |
| `facts.yml:43` | Facts \| retrieve current hostname without delegate | `command: hostname` (delegated to IDM master) | **READ-ONLY** | Keep; casing normalized (task 1.2) |
| `freeipa-client.yml:78` | Freeipa-client \| Get FreeIPA CA certificate serial number | shell: `kdestroy`/`kinit`/`ipa cert-find` | **READ-ONLY** (ticket-cache churn is not persistent system state) | Keep `changed_when: false` |
| `freeipa-client.yml:94` | Freeipa-client \| Retrieve FreeIPA CA certificate | shell writing `/etc/pki/ca-trust/source/anchors/ipa-ca.pem` | **STATE-CHANGING** (shortcut) | PEM captured to stdout; file written via idempotent `copy` module (tasks 3.1–3.2). The retrieval task itself becomes genuinely read-only → its `changed_when: false` is now accurate, not a shortcut |
| `freeipa-client.yml:103` | Update CA trust | `command: update-ca-trust` | **STATE-CHANGING** (shortcut) | Gated on the anchor copy having reported changed; blanket `false` removed — runs only when the trust store actually needs rebuilding, where default changed=true is accurate (task 3.3) |
| `freeipa-client.yml:129` | Freeipa-client \| restart systemd-resolved | `systemd: state=restarted` + blanket `false` | **STATE-CHANGING** (unconditional restart masked by shortcut) | Gated on the `head.conf` template having been modified; blanket `false` removed — re-runs skip it entirely (task 3.4) |
| `freeipa-client-delete.yml:10` | Freeipa-client-delete \| call to ipa client uninstall | `command: ipa-client-install --uninstall` (`failed_when: false`) | **STATE-CHANGING** (shortcut) | Gated on IPA client presence; `changed_when: <result>.rc == 0` so changed is reported exactly when an uninstall actually happened (tasks 4.1–4.2) |
| `freeipa-client-delete.yml:33` | Freeipa-client-delete \| reinstall krb5-libs | `command: dnf -y reinstall krb5-libs` | **STATE-CHANGING** (shortcut) | Gated on the same presence check; blanket `False` removed — runs only after an uninstall, where default changed=true is accurate (task 4.3) |

**Summary**: 3 read-only usages kept (`false` is the exact answer for them); 6 state-changing shortcuts fixed with conditional guards and/or exact change reporting. No other `changed_when` exists in `templates/`, `defaults/`, `vars/`, or `meta/`.
