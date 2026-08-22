## Purpose

Functionally verify, via the molecule scenarios, that a host joined by `tcharl.ansible_securehost` works as a domain member — Kerberos authentication succeeds, the FreeIPA CA is trusted by the system, and DNS is wired through `systemd-resolved` — so enrollment and trust regressions are caught rather than only config-file presence being asserted.

## ADDED Requirements

### Requirement: Kerberos authentication works on the client
The client SHALL be able to authenticate to the KDC and obtain a valid Kerberos ticket after the role runs, proving the host functions as a domain member rather than merely being configured.

#### Scenario: kinit with the admin principal succeeds
- **WHEN** a molecule test runs `kinit` for the admin principal on the client
- **THEN** the command succeeds (rc=0)

#### Scenario: A valid ticket for the realm is reported
- **WHEN** a molecule test runs `klist` after a successful `kinit` on the client
- **THEN** `klist` succeeds and reports a ticket for the domain realm

### Requirement: The client holds a Kerberos keytab and realm configuration
The client SHALL have a host keytab installed and a `krb5.conf` configured with the domain realm, so host-based authentication is possible.

#### Scenario: The host keytab is present
- **WHEN** a molecule test inspects the client's keytab location
- **THEN** a keytab file is present (`/etc/krb5.keytab` or `/var/lib/krb5.keytab`)

#### Scenario: krb5.conf contains the realm
- **WHEN** a molecule test inspects `/etc/krb5.conf` on the client
- **THEN** the file contains the domain realm

### Requirement: The FreeIPA CA anchor is installed and trusted
The client SHALL have the FreeIPA CA anchor certificate installed and the system trust store SHALL trust it, so that the IDM server's certificate chain validates.

#### Scenario: The CA anchor is installed
- **WHEN** a molecule test inspects `/etc/pki/ca-trust/source/anchors/ipa-ca.pem` on the client
- **THEN** the file is present and non-empty

#### Scenario: The IDM certificate chain validates
- **WHEN** a molecule test runs `openssl s_client` against the IDM server's HTTPS port using the system trust store
- **THEN** the certificate chain validates with `Verify return code: 0 (ok)`

### Requirement: The client is wired for domain host resolution
The client SHALL make the IDM server resolvable for domain services: a `/etc/hosts` entry for the IDM hostname and DNS delegated to `systemd-resolved`.

#### Scenario: /etc/hosts contains the IDM entry
- **WHEN** a molecule test inspects `/etc/hosts` on the client
- **THEN** it contains a hostname entry for the IDM server

#### Scenario: DNS is delegated to systemd-resolved
- **WHEN** a molecule test inspects `/etc/resolv.conf` on the client
- **THEN** it is a symlink to the `systemd-resolved` stub resolver
