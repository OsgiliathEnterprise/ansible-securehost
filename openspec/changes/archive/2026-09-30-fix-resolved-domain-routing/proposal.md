# Proposal

## Why

The uncommitted `head.j2` change (route the domain and the private subnet's reverse zone through the IDM DNS server instead of the public fallback) broke `test_client_reach_idm`: on the client, `resolvectl status | grep -c 'osgiliath.test'` returns `0`. The template emits a combined line `DNS=<idm_ip> Domains=...`, but systemd-resolved does not support inline `Domains=` after a server address — every word of a `DNS=` value must parse as an address, so the domain tokens are rejected (journal warning) and **no search/route domains get configured at all**. The client therefore no longer routes any lookups for `osgiliath.test` or its private reverse zone through the IDM.

## What Changes

- Rewrite `templates/systemd-resolved.conf.d/head.j2` to use only supported `resolved.conf.d` syntax: separate `DNS=` lines (IDM server first, public fallback second) and a standalone `Domains=` line listing the domain and the CIDR-derived reverse zone as route-only (`~`) entries.
- Keep the existing CIDR → reverse-zone computation (`securehost_additional_dns_cidr`, octet-aligned prefixes).
- Update `molecule/default/tests/test_domain_wiring.py::test_resolved_head_conf_bind_scoped`: it currently asserts the broken combined-line syntax (a `DNS=` line containing `Domains=...in-addr.arpa`); re-point it at a standalone `Domains=` line containing the reverse zone. The other two content tests (`two_nameservers`, `public_fallback`) and `test_ipa_client.py::test_client_reach_idm` stay as-is and must pass again.
- Fix the stale comment on `securehost_additional_dns_cidr` in `defaults/main.yml` (it says "this client's /24" but the default derives from `securehost_idm_ip`).

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `securehost-verification`: add a requirement that the client's `systemd-resolved` configuration actually routes domain and private-subnet lookups via the IDM server — `head.conf` uses only supported syntax (separate `DNS=`/`Domains=` keys), lists both nameservers, carries route-only domains for the domain and the reverse zone, and `resolvectl status` reports them.

## Impact

- **Affected code**:
  - `templates/systemd-resolved.conf.d/head.j2` — template rewrite (syntax only; same variables: `idm_ip_to_set`, `domain`, `securehost_additional_dns_cidr`).
  - `defaults/main.yml` — comment fix on `securehost_additional_dns_cidr`.
  - `molecule/default/tests/test_domain_wiring.py` — one assertion re-pointed (shared by the `default` and `parallels` scenarios via symlink).
- **Behavior**: restored/correct DNS routing on joined clients: forward lookups for `<company_domain>` and PTR lookups for the private subnet are routed through the IDM's bind; `8.8.8.8` remains the public fallback. No task/handler changes — the existing template task + `Restart systemd-resolved` handler already apply the new content idempotently (role-idempotence spec unaffected).
- **Assumptions**:
  - The feature intent of the last change is preserved: route domain + private-subnet reverse lookups via IDM, keep `8.8.8.8` as fallback.
  - Both domains are kept route-only (`~`) to avoid changing single-label search-suffix behavior (matches the previously working configuration).
  - True per-server scoping ("server X only for domain Y") is not expressible in `resolved.conf.d`; with both servers global and IDM listed first, routing is best-effort (IDM preferred, fallback on failure). Strict isolation via networkd/D-Bus is out of scope.
