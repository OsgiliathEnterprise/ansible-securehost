# Tasks

## 1. Template and defaults fix

- [x] 1.1 Rewrite `templates/systemd-resolved.conf.d/head.j2` to render separate lines — `DNS={{ idm_ip_to_set }}`, `DNS=8.8.8.8`, and a standalone `Domains=~{{ domain }} ~<reverse-zone>.in-addr.arpa` line (keep the existing `_cidr`/`_octets`/`_n` sets for the CIDR → reverse-zone computation) — and verify by rendering locally with sample values (`python3 -c "import jinja2; print(jinja2.Template(open('templates/systemd-resolved.conf.d/head.j2').read()).render(idm_ip_to_set='192.168.50.5', domain='osgiliath.test', securehost_idm_dns_cidr='192.168.50.0/24'))"`) that the output has exactly two `DNS=` lines (IDM first, then `8.8.8.8`), one `Domains=` line with both route-only entries, and no `Domains=` token on any `DNS=` line
- [x] 1.2 Fix the stale comment on `securehost_idm_dns_cidr` in `defaults/main.yml` (the default derives from `securehost_idm_ip`, not "this client's /24") and verify via `git diff defaults/main.yml` that only comment lines changed — the variable value expression is untouched

## 2. Test reconciliation (`molecule/default/tests/test_domain_wiring.py`)

- [x] 2.1 Re-point `test_resolved_head_conf_bind_scoped` at a standalone `Domains=` line containing the reverse zone (e.g. `grep '^Domains=' /etc/systemd/resolved.conf.d/head.conf | grep -c 'in-addr.arpa'` == 1) and verify the assertion matches the rendered template shape from task 1.1 and the file passes syntax/lint (`tox -e lint`)
- [x] 2.2 Add `test_resolved_head_conf_no_inline_domains` asserting no `DNS=` line contains a `Domains=` token (e.g. `grep '^DNS=' /etc/systemd/resolved.conf.d/head.conf | grep -c 'Domains='` yields no match) and verify it fails against the old broken template content while passing against the fixed rendering from task 1.1

## 3. End-to-end verification

- [x] 3.1 Run `uv tool run --python 3.13 --with tox tox -e lint` and verify yamllint, flake8, and ansible-lint all pass
- [ ] 3.2 Run the full default-scenario cycle (`uv tool run --python 3.13 --with tox tox -e test-exec`) and verify `test_ipa_client.py::test_client_reach_idm`, all three head.conf tests in `test_domain_wiring.py`, and the new no-inline-domains test pass
- [ ] 3.3 On the live client during/after converge, run `resolvectl status` (global section shows `~osgiliath.test` and `~<reverse-zone>.in-addr.arpa` under DNS Domain), check `journalctl -u systemd-resolved` for "Failed to add DNS server address" warnings (must be absent), and confirm functional routing with `dig +short idm.osgiliath.test` plus a PTR lookup of a private-subnet IP resolving via the IDM server
- [ ] 3.4 Re-run converge (`uv tool run --python 3.13 --with tox tox -e idempotence`) and verify no task reports changed for `head.conf` or the `systemd-resolved` restart (role-idempotence spec unchanged)
- [ ] 3.5 Run the parallels scenario cycle (`uv tool run --python 3.13 --with tox tox -e test-exec-monorepo -- --scenario-name=parallels`) and verify the same DNS tests pass there, since `molecule/parallels/tests` symlinks to the shared test dir
