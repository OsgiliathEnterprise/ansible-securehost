testinfra_hosts = ["idm.osgiliath.test"]


def test_ipa_installed_on_server(host):
    with host.sudo():
        command = """systemctl status ipa.service | grep -c 'active'"""
        cmd = host.run(command)
    assert int(cmd.stdout.rstrip()) >= 1


def test_ipa_firewalld_dns_service_is_open(host):
    with host.sudo():
        command = """firewall-cmd --list-services | grep -c 'dns'"""
        cmd = host.run(command)
    assert int(cmd.stdout.rstrip()) >= 1


def test_ipa_firewalld_freeipa_ldap_service_is_open(host):
    with host.sudo():
        command = """firewall-cmd --list-services | grep -c 'freeipa-ldap'"""
        cmd = host.run(command)
    assert int(cmd.stdout.rstrip()) >= 1


def test_ipa_firewalld_freeipa_ldaps_service_is_open(host):
    with host.sudo():
        command = """firewall-cmd --list-services | grep -c 'freeipa-ldaps'"""
        cmd = host.run(command)
    assert int(cmd.stdout.rstrip()) >= 1


def test_ipa_firewalld_freeipa_https_service_is_open(host):
    with host.sudo():
        command = """firewall-cmd --list-services | grep -c 'https'"""
        cmd = host.run(command)
    assert int(cmd.stdout.rstrip()) >= 1


def test_client_service_is_created(host):
    command = """echo '123ADMin' | \
    kinit admin > /dev/null && \
    ipa host-find client.osgiliath.test | \
    grep -c ': client.osgiliath.test'"""
    cmd = host.run(command)
    assert int(cmd.stdout.rstrip()) >= 1
