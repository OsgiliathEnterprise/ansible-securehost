# Delta Spec: role-idempotence

## Purpose

Guarantees that re-running `tcharl.ansible_securehost` on an already-configured host is a no-op (zero changed tasks) and that molecule scenarios verify this property via the `idempotence` action, so drift and spurious changes are visible instead of masked by blanket `changed_when: false`.

## ADDED Requirements

### Requirement: Re-running the role reports zero changed tasks
When the role is executed a second time on a host it has already fully configured (same variables), every task belonging to this role SHALL report `ok` or be skipped, and the run SHALL report zero changed tasks for the role's own tasks.

#### Scenario: Second converge on an already-joined client
- **WHEN** molecule converges the default scenario a second time after a successful first converge (the idempotence action)
- **THEN** no task belonging to `tcharl.ansible_securehost` reports changed, and the idempotence check passes

#### Scenario: Re-run does not restart services or reload configuration needlessly
- **WHEN** the role is re-run on a host whose NetworkManager already uses systemd-resolved as its DNS resolver, whose CA anchor certificate is unchanged, and whose `head.conf` template content is unchanged
- **THEN** no `nmcli general reload`, no `update-ca-trust`, and no `systemd-resolved` restart are executed

### Requirement: State-changing commands report changes accurately
Every command or shell task that can modify system state SHALL either be guarded so it runs only when the desired state is not yet present, or carry a `changed_when` expression that evaluates to true exactly when the task modified the system. A blanket `changed_when: false` SHALL NOT be used on such tasks.

#### Scenario: CA anchor certificate already up to date
- **WHEN** the role runs and the FreeIPA CA certificate at `/etc/pki/ca-trust/source/anchors/ipa-ca.pem` is identical to the one served by the IDM server
- **THEN** no task reports changed for the certificate retrieval, `update-ca-trust`, or the systemd-resolved restart

#### Scenario: CA anchor certificate differs from the server's
- **WHEN** the role runs and the stored CA anchor certificate differs from the one served by the IDM server
- **THEN** the certificate write task reports changed, `update-ca-trust` is executed, and `systemd-resolved` is restarted

#### Scenario: NetworkManager already uses systemd-resolved
- **WHEN** the role runs on a host where NetworkManager's DNS resolver is already systemd-resolved
- **THEN** the NetworkManager reload task is skipped (or reports ok) and no changed state is reported for it

### Requirement: Read-only commands are marked as never changing
Commands that only read system state (e.g. retrieving the hostname, querying the CA certificate serial number) SHALL use `changed_when: false` so they never report changed, regardless of how often they run.

#### Scenario: Fact-gathering re-run
- **WHEN** the role is re-run and fact-gathering tasks execute read-only commands such as `hostname` or a CA serial number query
- **THEN** those tasks report ok (never changed)

### Requirement: Client removal flow is guarded by client presence
The IPA client uninstall (`ipa-client-install --uninstall`) and the subsequent `krb5-libs` reinstall SHALL execute only when an IPA client is actually present on the host, and each SHALL report changed accurately. Re-invoking the removal flow on a host without an IPA client SHALL NOT report changed for those steps.

#### Scenario: Removal flow on a host with no IPA client
- **WHEN** the reset/delete flow runs on a host where no IPA client is installed
- **THEN** the uninstall and `krb5-libs` reinstall tasks are skipped or report ok, not changed

### Requirement: Molecule scenarios verify idempotence
Every molecule scenario of this role SHALL include the `idempotence` action in its `test_sequence`. Tasks belonging to dependencies that are known to be non-idempotent outside this role's control SHALL be excluded from the idempotence check using the molecule-native tag `molecule-idempotence-notest` (skipped only during the idempotence action), and each such exclusion SHALL carry a comment referencing the pending upstream fix.

#### Scenario: Molecule test sequence includes idempotence
- **WHEN** any scenario's `test_sequence` is inspected (`default`, `kvm`, `parallels`)
- **THEN** it contains the `idempotence` action between `converge` and `side_effect`

#### Scenario: Known non-idempotent dependencies are excluded only from idempotence
- **WHEN** the role's converge includes a dependency tagged `molecule-idempotence-notest` (the upstream `freeipa.ansible_freeipa.ipaclient` include pending freeipa/ansible-freeipa PR #1432, and the `tcharl.etchost_append` include pending its own fix)
- **THEN** that dependency runs normally during `converge`, is skipped only during the `idempotence` action, and a comment at the tag references the pending upstream fix
