## Why

The molecule scenarios only verify config-file *presence* on the client (IPA installed, realm/domain in `/etc/ipa/default.conf`, DNS reachability) and host *registration* on the server. They do not functionally verify that the host actually *works* as a domain member: that Kerberos authentication succeeds, that the FreeIPA CA is trusted by the system, or that DNS is wired through `systemd-resolved`. A regression that leaves a host enrolled on paper but unable to authenticate or trust the CA would pass verification silently.

## What Changes

- Add functional verification tests to the shared molecule test dir (`molecule/default/tests/`, which `molecule/parallels/tests` symlinks to) targeting the **client** host:
  - **Kerberos auth**: `kinit` with the admin principal succeeds (rc=0) and `klist` reports a valid ticket for the realm.
  - **Kerberos client artifacts**: a host keytab is present (`/etc/krb5.keytab` or `/var/lib/krb5.keytab`) and `/etc/krb5.conf` contains the domain realm.
  - **CA trust**: the FreeIPA CA anchor is installed at `/etc/pki/ca-trust/source/anchors/ipa-ca.pem` (present, non-empty) and the IDM server's certificate chain validates against the system trust store (`openssl s_client` reports `Verify return code: 0 (ok)`).
  - **Domain wiring**: `/etc/hosts` contains the IDM hostname entry and DNS is delegated to `systemd-resolved` (`/etc/resolv.conf` is a symlink to the stub resolver).
- The new tests run in **both** the `default` (vagrant/virtualbox, Fedora 44) and `parallels` (parallels, Fedora 43) scenarios, since they share the test directory.
- No role task changes. No new dependencies beyond tools already present on a joined client (`krb5` `kinit`/`klist`, `openssl`, coreutils).

## Capabilities

### New Capabilities
- `securehost-verification`: The molecule scenarios functionally verify a joined host — that Kerberos authentication works, the FreeIPA CA is trusted by the system, and DNS/domain wiring is correct — rather than only asserting config-file presence.

### Modified Capabilities
- (none)

## Impact

- **Affected code**: `molecule/default/tests/` — new test files `test_kerberos.py`, `test_ca_trust.py`, `test_domain_wiring.py`. `molecule/parallels/tests` picks them up via its existing symlink to `../default/tests`.
- **Behavior**: the `verify` step of both molecule scenarios now fails on a regression in enrollment, Kerberos, or CA trust, instead of passing on config presence alone.
- **Assumption**: the `kinit` test uses the molecule test admin password (`123ADMin`, from `prepare.yml`), consistent with the existing `test_ipa_server.py` pattern.
- **Hostnames**: tests target `client.osgiliath.test` / `idm.osgiliath.test`, matching the existing tests and both scenario topologies.
