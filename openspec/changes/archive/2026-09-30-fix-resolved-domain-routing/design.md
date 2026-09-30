# Design

## Context

See proposal.md for motivation. Current state:

- `tasks/freeipa-client.yml` templates `templates/systemd-resolved.conf.d/head.j2` to `/etc/systemd/resolved.conf.d/head.conf` (vars: `idm_ip_to_set`, `domain`) and notifies the existing `Restart systemd-resolved` handler — no task/handler changes are needed for a template-content fix.
- The uncommitted template renders a **combined line**: `DNS=<idm_ip> Domains={{ domain }} ~{{ domain }} <rev>.in-addr.arpa` plus `DNS=8.8.8.8`.
- Client topology (both molecule scenarios): DHCP on an isolated private network, NetworkManager delegating DNS to systemd-resolved (`tasks/prereq.yml`). No per-link DNS servers or domains are provided by DHCP in this setup, so the global `[Resolve]` configuration is what applies.

### Root cause (verified against systemd source)

1. `resolved.conf.d` does **not** support inline `Domains=` after a server address. The man page (`resolved.conf(5)`) defines `DNS=` as "a space-separated list of IPv4 and IPv6 addresses" with only optional `:port`, `%ifname`, `#sni` suffixes — no domain tokens.
2. In the systemd source, `manager_parse_dns_server_string_and_warn()` (`src/resolve/resolved-dns-server.c`) splits a `DNS=` value word-by-word and parses each word as an address via `in_addr_port_ifindex_name_from_string_auto()`. Words that fail are logged ("Failed to add DNS server address '%s', ignoring") and **dropped**. So in the current template, `Domains=osgiliath.test`, `~osgiliath.test` and `<rev>.in-addr.arpa` are all rejected → the effective configuration is two global servers (`<idm_ip>`, `8.8.8.8`) and **zero** domains.
3. With no domains configured, `resolvectl status` prints no "DNS Domain" line containing `osgiliath.test` → `test_client_reach_idm` (`grep -c 'osgiliath.test'`) returns 0.
4. Why the previous template passed: its standalone `Domains=~osgiliath.test` line is parsed by `config_parse_search_domains()` → `manager_add_search_domain_by_string()`, which explicitly treats a leading `~` as a **route-only** marker (`route_only = *domain == '~'`). Route-only domains are displayed in the global section of `resolvectl status` under "DNS Domain" with their `~` prefix (`format_search_domains()` in `src/resolve/resolvectl.c`) — so the grep matched.
5. Multiple `DNS=` lines are merged as a list, in file order (man page: "entries are collected as they occur"), so listing the IDM first makes it the preferred global server with failover to the fallback.

## Goals / Non-Goals

**Goals:**

- Restore a valid `head.conf` so domains are actually applied by systemd-resolved and `test_client_reach_idm` passes again.
- Preserve the feature intent of the last change: forward lookups for `<company_domain>` and PTR lookups for the private subnet's reverse zone route through the IDM server; `8.8.8.8` remains the public fallback.
- Reconcile the content-assertion tests in `test_domain_wiring.py` with valid syntax, including a regression guard against inline-domain lines.

**Non-Goals:**

- True per-server domain scoping ("server X only for domain Y") — not expressible in `resolved.conf.d`; would require networkd `.network` files or D-Bus (`SetLinkDomains`). Out of scope; see Risks.
- Changing how the client obtains its IP/DHCP, NetworkManager wiring, or the IPA enrollment flow.
- Supporting non-octet-aligned CIDR prefixes for the reverse-zone computation (existing constraint).

## Decisions

### D1 — Template shape: separate `DNS=` lines + standalone route-only `Domains=` line

Rendered target:

```ini
[Resolve]
DNS={{ idm_ip_to_set }}
DNS=8.8.8.8
Domains=~{{ domain }} ~{{ _octets[:_n][::-1] | join('.') }}.in-addr.arpa
```

Rationale: the only syntax resolved actually applies; multiple `DNS=` lines merge in order (IDM first = preferred server). The CIDR → reverse-zone computation (`_cidr`, `_octets`, `_n` sets) is kept unchanged.

**Alternative considered:** one combined `DNS=<idm> 8.8.8.8` line + `Domains=...`. Functionally equivalent, but the existing (uncommitted) test `test_resolved_head_conf_two_nameservers` asserts exactly two lines matching `^DNS=` — keeping two separate lines preserves that test unchanged and makes preference order explicit in the file.

### D2 — Both domains route-only (`~`)

`Domains=~<domain> ~<rev>.in-addr.arpa`. A bare (non-`~`) domain would additionally become a **search suffix** for single-label lookups, changing behavior versus the previously working configuration; `~` keeps them routing-only. Matches the old template's semantics (`~{{ domain }}`).

### D3 — Keep `securehost_additional_dns_cidr` default as-is; fix only the stale comment

The default derives from `securehost_idm_ip | ansible.utils.ipsubnet(24)` (the /24 containing the IDM). The comment in `defaults/main.yml` says "this client's /24" — stale and misleading. Fix the comment to describe the actual default; no value change, so no scenario overrides are affected.

### D4 — Test reconciliation in `molecule/default/tests/test_domain_wiring.py`

- `test_resolved_head_conf_bind_scoped`: currently asserts a `DNS=` line containing both `Domains=` and `in-addr.arpa` (i.e., the broken syntax). Re-point it at a standalone `Domains=` line: `grep '^Domains=' head.conf | grep -c 'in-addr.arpa'` == 1.
- Add `test_resolved_head_conf_no_inline_domains`: `grep '^DNS=' head.conf | grep -c 'Domains='` == 0 — the regression guard for exactly this bug class (spec scenario "head.conf contains no inline domains after a server address").
- `test_resolved_head_conf_two_nameservers`, `test_resolved_head_conf_public_fallback`, and `test_ipa_client.py::test_client_reach_idm` stay unchanged.
- `molecule/parallels/tests` is a symlink to `../default/tests`, so both scenarios are covered automatically.

### D5 — No task/handler changes

The existing template task + `Restart systemd-resolved` handler already apply new content and restart only when the file changed (idempotent re-runs per the `role-idempotence` spec). Nothing else in the role references `head.conf`.

## Risks / Trade-offs

- [Global route-only domains are documented as effective "only when suitable per-link DNS servers are known"] → In this scenario no per-link servers exist, so the global configuration is what applies; the previously working template proves the mechanism functions here. Mitigation: verify empirically on a live client during apply — `resolvectl status` (global section shows `~<domain>` and `~<rev>.in-addr.arpa`) plus functional checks (`dig`/`host` for the IDM hostname and a PTR lookup of a private IP, expecting answers from the IDM server).
- [Best-effort server selection] With both servers global, resolved prefers the first-listed (IDM) and fails over to `8.8.8.8` on error; queries are not strictly isolated per domain/server. Mitigation: accepted trade-off — identical semantics to the previously working configuration; strict isolation would need networkd/D-Bus (future work).
- [Silent-drop failure mode] If future template edits reintroduce invalid tokens, resolved drops them with only a journal warning. Mitigation: the new `no_inline_domains` test plus an apply-phase check of `journalctl -u systemd-resolved` for "Failed to add DNS server address" warnings (must be absent).
- [CIDR override with non-octet-aligned prefix] yields a wrong reverse zone (e.g., `/25`). Pre-existing constraint, documented in the default's comment; unchanged by this fix.

## Migration Plan

1. Apply template + defaults-comment + test edits (single converge applies them; handler restarts `systemd-resolved` only when content changed).
2. Rollback: revert `head.j2` to the last committed version (`git checkout -- templates/systemd-resolved.conf.d/head.j2`) and re-converge — restores the previously working configuration.
3. No data migration, no state cleanup needed; `head.conf` is fully regenerated from the template on each converge.

## Open Questions

None — the empirical routing behavior (D1/D-risk 1) is a verification step during apply, not an unknown that changes the approach: the previously working configuration already exercised this exact mechanism in both scenarios.
