# Spec Delta

## ADDED Requirements

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
