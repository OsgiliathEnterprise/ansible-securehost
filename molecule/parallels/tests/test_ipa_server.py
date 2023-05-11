testinfra_hosts = ["idm.osgiliath.test"]


def test_client_service_is_created(host):
    command = """echo '123ADMin' | \
    kinit admin > /dev/null && \
    ipa host-find client.osgiliath.test | \
    grep -c ': client.osgiliath.test'"""
    cmd = host.run(command)
    assert int(cmd.stdout.rstrip()) >= 1
