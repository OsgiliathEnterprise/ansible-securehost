testinfra_hosts = ["client.osgiliath.test"]


def test_ca_anchor_installed(host):
    command = """test -s /etc/pki/ca-trust/source/anchors/ipa-ca.pem"""
    with host.sudo():
        cmd = host.run(command)
    assert cmd.rc == 0


def test_idm_cert_chain_validates(host):
    command = """echo | openssl s_client -connect idm.osgiliath.test:443 \
    -servername idm.osgiliath.test 2>/dev/null | \
    grep -c 'Verify return code: 0'"""
    with host.sudo():
        cmd = host.run(command)
    assert cmd.rc == 0
    assert int(cmd.stdout.rstrip()) >= 1
