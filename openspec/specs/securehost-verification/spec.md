# securehost-verification Specification

## Purpose

Functionally verify, via the molecule scenarios, that a host joined by `tcharl.ansible_securehost` works as a domain member — Kerberos authentication succeeds, the FreeIPA CA is trusted by the system, and DNS is wired through `systemd-resolved` — so enrollment and trust regressions are caught rather than only config-file presence being asserted.

## Requirements

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

### Requirement: The client routes domain and private-subnet DNS lookups via the IDM server
The client SHALL configure `systemd-resolved` so that lookups for the company domain and for the private subnet's reverse zone are routed through the IDM's DNS server, with a public fallback server (`8.8.8.8`) for everything else. The generated `/etc/systemd/resolved.conf.d/head.conf` SHALL use only syntax supported by `resolved.conf.d`: separate `DNS=` lines containing server addresses only, and standalone `Domains=` lines. Domains MUST NOT be inlined after a server address on a `DNS=` line — the resolver rejects such tokens as invalid addresses and silently drops them, leaving no domains configured.

#### Scenario: head.conf lists both nameservers in preference order
- **WHEN** a molecule test inspects `/etc/systemd/resolved.conf.d/head.conf` on the client
- **THEN** it contains exactly two `DNS=` lines — the first carrying the IDM server address, the second being exactly `DNS=8.8.8.8`

#### Scenario: head.conf carries route-only domains for the domain and the reverse zone
- **WHEN** a molecule test inspects `/etc/systemd/resolved.conf.d/head.conf` on the client
- **THEN** a standalone `Domains=` line lists both the company domain and the private subnet's reverse zone (an `*.in-addr.arpa` name), each prefixed with `~` to mark it route-only

#### Scenario: head.conf contains no inline domains after a server address
- **WHEN** a molecule test inspects `/etc/systemd/resolved.conf.d/head.conf` on the client
- **THEN** no `DNS=` line contains a `Domains=` token — every word following a `DNS=` key is a bare server address

#### Scenario: The resolver reports the domain for the client
- **WHEN** a molecule test runs `resolvectl status` on the client
- **THEN** the output contains the company domain, proving the route-only domains were actually applied by the resolver rather than only written to the file
