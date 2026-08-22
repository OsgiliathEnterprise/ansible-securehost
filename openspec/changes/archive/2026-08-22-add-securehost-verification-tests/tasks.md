## 1. Kerberos verification tests (`test_kerberos.py`)

- [x] 1.1 Create `molecule/default/tests/test_kerberos.py` with `testinfra_hosts = ["client.osgiliath.test"]` and `test_kerberos_kinit_succeeds` that runs `echo '123ADMin' | kinit admin` via `host.sudo()` and asserts `rc == 0`. Verify: the file is valid Python (`python -m py_compile`) and defines `test_kerberos_kinit_succeeds`.
- [x] 1.2 Add `test_kerberos_ticket_valid` to `test_kerberos.py` that runs `echo '123ADMin' | kinit admin && klist` and asserts `rc == 0` **and** the output contains the realm `OSGILIATH.TEST`. Verify: the file is valid Python and defines `test_kerberos_ticket_valid`.
- [x] 1.3 Add `test_client_keytab_present` to `test_kerberos.py` that asserts (via `host.sudo()`) `/etc/krb5.keytab` **or** `/var/lib/krb5.keytab` exists. Verify: the file is valid Python and defines `test_client_keytab_present`.
- [x] 1.4 Add `test_krb5_conf_has_realm` to `test_kerberos.py` that asserts `/etc/krb5.conf` exists and contains `OSGILIATH.TEST`. Verify: the file is valid Python and defines `test_krb5_conf_has_realm`.

## 2. CA trust verification tests (`test_ca_trust.py`)

- [x] 2.1 Create `molecule/default/tests/test_ca_trust.py` with `testinfra_hosts = ["client.osgiliath.test"]` and `test_ca_anchor_installed` that asserts `/etc/pki/ca-trust/source/anchors/ipa-ca.pem` exists and is non-empty. Verify: the file is valid Python and defines `test_ca_anchor_installed`.
- [x] 2.2 Add `test_idm_cert_chain_validates` to `test_ca_trust.py` that runs `echo | openssl s_client -connect idm.osgiliath.test:443 -servername idm.osgiliath.test` (system trust store, no `-CAfile`) and asserts the output contains `Verify return code: 0`. Verify: the file is valid Python and defines `test_idm_cert_chain_validates`; if the live verify code is not `0 (ok)`, inspect the presented chain and adjust the assertion.

## 3. Domain wiring verification tests (`test_domain_wiring.py`)

- [x] 3.1 Create `molecule/default/tests/test_domain_wiring.py` with `testinfra_hosts = ["client.osgiliath.test"]` and `test_etc_hosts_has_idm_entry` that asserts `/etc/hosts` contains `idm.osgiliath.test`. Verify: the file is valid Python and defines `test_etc_hosts_has_idm_entry`.
- [x] 3.2 Add `test_dns_delegated_to_resolved` to `test_domain_wiring.py` that asserts `readlink /etc/resolv.conf` output contains `stub-resolv.conf`. Verify: the file is valid Python and defines `test_dns_delegated_to_resolved`; if the box does not produce the symlink, adjust the assertion to match the actual NetworkManager/resolved wiring.

## 4. Scenario verification and lint

- [ ] 4.1 Bring up the `default` scenario (`molecule create` + `molecule converge --scenario-name=default`, then `molecule verify --scenario-name=default`; or `molecule test --scenario-name=default` for the full sequence) and confirm all 8 new tests are collected and pass on Fedora 44. Verify: the verify run reports the 8 new test functions collected and passing. _(Out of scope: this change was verified on macOS, which maps to the `parallels` scenario per the host-OS scenario rule; `default`/virtualbox targets Windows. Intentionally not run.)_
- [x] 4.2 Bring up the `parallels` scenario and confirm the same 8 tests are collected and pass on Fedora 43 via the `molecule/parallels/tests → ../default/tests` symlink (no per-scenario test files). Verify: the verify run for `parallels` reports the 8 new test functions collected and passing.
- [x] 4.3 Run the `lint` tox env (`tox -e lint`) and confirm the three new test files pass `flake8` (and do not introduce `yamllint`/`ansible-lint` regressions). Verify: `tox -e lint` exits 0.
