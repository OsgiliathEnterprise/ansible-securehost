testinfra_hosts = ["client.osgiliath.test"]


def test_ipa_installed_on_client(host):
    command = """ipa --version | grep -c 'API_VERSION'"""
    cmd = host.run(command)
    assert '1' in cmd.stdout


def test_ipa_realm_configured_client(host):
    command = """cat /etc/ipa/default.conf | \
    grep -c 'realm = OSGILIATH.TEST'"""
    cmd = host.run(command)
    assert '1' in cmd.stdout


def test_ipa_domain_configured_client(host):
    command = """cat /etc/ipa/default.conf | \
    grep -c 'domain = osgiliath.test'"""
    cmd = host.run(command)
    assert '1' in cmd.stdout


def test_rpc_uri_configured_client(host):
    command = """cat /etc/ipa/default.conf | \
    grep -c 'xmlrpc_uri = https://idm.osgiliath.test/ipa/xml'"""
    cmd = host.run(command)
    assert '1' in cmd.stdout
