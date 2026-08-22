## Context

The molecule scenarios for `tcharl.ansible_securehost` use `testinfra` as the verifier. Both the `default` (vagrant/virtualbox, Fedora 44) and `parallels` (parallels, Fedora 43) scenarios share the same test directory: `molecule/parallels/tests` is a symlink to `../default/tests`. Existing tests (`test_ipa_client.py`, `test_ipa_server.py`) assert config-file presence and server-side host registration only. See proposal.md for the motivation.

Key constraints:
- Tests run over SSH via testinfra; privileged commands use `host.sudo()`, matching the existing test pattern.
- The `kinit` test must use a known credential. The molecule `prepare.yml` provisions the realm with the test admin password (`123ADMin`), and `test_ipa_server.py` already uses `echo '123ADMin' | kinit admin`.
- Both scenarios target `client.osgiliath.test` (client) and `idm.osgiliath.test` (server).

## Goals / Non-Goals

**Goals:**
- Add functional, client-side verification tests that prove Kerberos auth works, the FreeIPA CA is trusted by the system, and DNS/domain wiring is correct.
- Place tests in the shared test dir so both scenarios run them with no duplication.
- Keep tests robust to per-run shell-session isolation and to the Fedora 43/44 difference.

**Non-Goals:**
- No changes to role tasks or handlers — this is verification-only.
- No new server-side tests (host registration is already covered by `test_ipa_server.py`).
- No hostname parameterization — follow the existing hard-coded `client.osgiliath.test` / `idm.osgiliath.test` convention.
- No tests for the delete/reset (`reset_ipa`) flow.

## Decisions

### D1: New test files in the shared dir, one per theme
Create three new files under `molecule/default/tests/`, each declaring `testinfra_hosts = ["client.osgiliath.test"]` at module level (overriding the `conftest.py` fallback, matching the existing files):
- `test_kerberos.py` — kinit success, valid ticket, keytab present, `krb5.conf` realm.
- `test_ca_trust.py` — CA anchor installed, IDM chain validates.
- `test_domain_wiring.py` — `/etc/hosts` IDM entry, `/etc/resolv.conf` symlinked to the `systemd-resolved` stub.

**Why new files over appending to `test_ipa_client.py`:** keeps the existing file untouched, groups tests by theme, and is trivially reviewable. `molecule/parallels/tests` picks them up via the existing symlink — no scenario changes needed.

### D2: Kerberos kinit uses the admin principal + molecule test password
`kinit` with `admin` and the `prepare.yml` password (`123ADMin`), consistent with `test_ipa_server.py`.

**Why:** simplest reliable credential that proves the client reaches the KDC and authenticates. **Alternative considered:** host-principal keytab kinit (`kinit -kt …`) — rejected because it requires knowing the exact principal and adds fragility; the keytab's *presence* is asserted separately.

### D3: Combine `kinit` and `klist` in one shell command
The ticket-validity test runs `echo '123ADMin' | kinit admin && klist` as a single command.

**Why:** each `host.run` is an isolated shell session; the ticket cache is per-uid on disk, but combining guarantees `klist` sees the ticket from the same `kinit` and avoids ordering dependence between separate test functions. The `kinit`-only test asserts `rc == 0`; the combined test asserts `rc == 0` **and** that the output contains the realm.

### D4: CA recognition via `openssl s_client` against the system trust store
`echo | openssl s_client -connect idm.osgiliath.test:443 -servername idm.osgiliath.test | grep 'Verify return code: 0'`, with **no** explicit `-CAfile`.

**Why:** the user's goal is that the CA is *recognized* by the system. Using the default trust store (populated by `update-ca-trust`) proves the anchor was actually added to the system bundle, not just written to disk. **Alternative considered:** `-CAfile …/ipa-ca.pem` — rejected because it only proves the anchor *can* verify the cert, not that the system *trusts* it (weaker).

### D5: Keytab presence checks both conventional locations
Assert `/etc/krb5.keytab` **or** `/var/lib/krb5.keytab` exists.

**Why:** the exact keytab path can vary by IPA version/distro; checking both avoids a false negative while still proving a host keytab was installed.

### D6: DNS delegation asserted via the `stub-resolv.conf` symlink
Assert `readlink /etc/resolv.conf` contains `stub-resolv.conf`.

**Why:** the `prereq.yml` task makes NetworkManager rely on `systemd-resolved`, whose observable result is `/etc/resolv.conf → /run/systemd/resolve/stub-resolv.conf`. This is the concrete, checkable consequence of that task. The separate `/etc/hosts` IDM-entry test covers the `tcharl.etchost_append` contribution.

## Risks / Trade-offs

- **Hard-coded test admin password in tests** → it is a molecule-only test credential (from `prepare.yml`) in an isolated lab environment, and matches the existing `test_ipa_server.py` pattern. Accepted for consistency; not a production secret.
- **`openssl s_client` verify code can be environment-sensitive (SNI, intermediate CA presentation)** → use `-servername idm.osgiliath.test`; if the chain does not validate to `0 (ok)` during the apply phase, inspect the presented chain and adjust the assertion (e.g., verify against the anchor explicitly as a fallback). Confirm during apply that the installed anchor is the issuer of the server cert.
- **`/etc/resolv.conf` symlink depends on NM/`systemd-resolved` config landing** → assert on the `stub-resolv.conf` substring rather than an exact absolute path; if the box does not produce the symlink, adjust the assertion during apply rather than weakening it to a no-op.
- **Fedora 43 vs 44 divergence between scenarios** → tests rely only on stable tools present on both (`krb5` `kinit`/`klist`, `openssl`, coreutils). No version-specific commands.
- **Ticket cache isolation across `host.run` calls** → mitigated by D3 (single combined command).

## Open Questions

None blocking. The keytab path (`D5`) and the exact `s_client` verify string (`D4`) are both handled leniently and confirmed/adjusted during the apply phase when the scenario is run.
