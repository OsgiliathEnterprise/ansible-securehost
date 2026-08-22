testinfra_hosts = ["client.osgiliath.test"]


def test_kerberos_kinit_succeeds(host):
    command = """echo '123ADMin' | \
    kinit admin > /dev/null"""
    with host.sudo():
        cmd = host.run(command)
    assert cmd.rc == 0


def test_kerberos_ticket_valid(host):
    command = """echo '123ADMin' | \
    kinit admin > /dev/null && \
    klist"""
    with host.sudo():
        cmd = host.run(command)
    assert cmd.rc == 0
    assert 'OSGILIATH.TEST' in cmd.stdout


def test_client_keytab_present(host):
    command = """test -e /etc/krb5.keytab -o -e /var/lib/krb5.keytab"""
    with host.sudo():
        cmd = host.run(command)
    assert cmd.rc == 0


def test_krb5_conf_has_realm(host):
    command = """test -e /etc/krb5.conf && \
    grep -c 'OSGILIATH.TEST' /etc/krb5.conf"""
    with host.sudo():
        cmd = host.run(command)
    assert cmd.rc == 0
    assert int(cmd.stdout.rstrip()) >= 1
