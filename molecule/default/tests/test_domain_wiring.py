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
