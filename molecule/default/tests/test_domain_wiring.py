testinfra_hosts = ["client.osgiliath.test"]


def test_etc_hosts_has_idm_entry(host):
    command = """grep -c 'idm.osgiliath.test' /etc/hosts"""
    with host.sudo():
        cmd = host.run(command)
    assert cmd.rc == 0
    assert int(cmd.stdout.rstrip()) >= 1


def test_dns_delegated_to_resolved(host):
    command = """readlink /etc/resolv.conf"""
    with host.sudo():
        cmd = host.run(command)
    assert 'stub-resolv.conf' in cmd.stdout


def test_resolved_head_conf_two_nameservers(host):
    command = r"""set -o pipefail && \
    grep -c '^DNS=' /etc/systemd/resolved.conf.d/head.conf"""
    with host.sudo():
        cmd = host.run(command)
    assert '2' in cmd.stdout


def test_resolved_head_conf_bind_scoped(host):
    command = r"""set -o pipefail && \
    grep '^Domains=' /etc/systemd/resolved.conf.d/head.conf | \
    grep -c 'in-addr.arpa'"""
    with host.sudo():
        cmd = host.run(command)
    assert '1' in cmd.stdout


def test_resolved_head_conf_public_fallback(host):
    command = r"""set -o pipefail && \
    grep -c '^DNS=8.8.8.8$' /etc/systemd/resolved.conf.d/head.conf"""
    with host.sudo():
        cmd = host.run(command)
    assert '1' in cmd.stdout


def test_resolved_head_conf_no_inline_domains(host):
    command = r"""set -o pipefail && \
    grep '^DNS=' /etc/systemd/resolved.conf.d/head.conf | \
    grep -c 'Domains=' || true"""
    with host.sudo():
        cmd = host.run(command)
    assert cmd.stdout.strip() == '0'
