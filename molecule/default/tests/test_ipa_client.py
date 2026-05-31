testinfra_hosts = ["client.osgiliath.test"]


def test_ipa_installed_on_client(host):
    command = """ipa --version | grep -c 'API_VERSION'"""
    cmd = host.run(command)
    assert '1' in cmd.stdout


def test_ipa_realm_configured_client(host):
    command = """cat /etc/ipa/default.conf | \
    grep -c 'realm = OSGILIATH.TEST'"""
    with host.sudo():
        cmd = host.run(command)
    assert '1' in cmd.stdout


def test_ipa_domain_configured_client(host):
    command = """cat /etc/ipa/default.conf | \
    grep -c 'domain = osgiliath.test'"""
    with host.sudo():
        cmd = host.run(command)
    assert '1' in cmd.stdout


def test_rpc_uri_configured_client(host):
    command = """cat /etc/ipa/default.conf | \
    grep -c 'xmlrpc_uri = https://idm.osgiliath.test/ipa/xml'"""
    with host.sudo():
        cmd = host.run(command)
    assert '1' in cmd.stdout


def test_client_reach_idm(host):
    command = """resolvectl status | \
    grep -c 'osgiliath.test'"""
    with host.sudo():
        cmd = host.run(command)
    assert '1' in cmd.stdout
