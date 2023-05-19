Ansible SecureHost
=========

* Galaxy: [![Ansible Galaxy](https://img.shields.io/badge/galaxy-tcharl.ansible_securehost-660198.svg?style=flat)](https://galaxy.ansible.com/tcharl/ansible_securehost)
* Lint & requirements: ![Molecule](https://github.com/OsgiliathEnterprise/ansible-securehost/workflows/Molecule/badge.svg)
* Tests: ![Molecule](https://app.travis-ci.com/OsgiliathEnterprise/ansible-securehost.svg?branch=master)

* Chat: [![Join the chat at https://gitter.im/OsgiliathEnterprise/platform](https://badges.gitter.im/OsgiliathEnterprise/platform.svg)](https://gitter.im/OsgiliathEnterprise/platform?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

Configure a freeipa client with a minimum of information

Requirements
------------

Like any other platform roles, executing `tox -e pipdep`, then `tox -e dependency`

Role Variables
--------------

Same as [freeipa client](https://github.com/freeipa/ansible-freeipa)
Note that you'll also need a freeipa-server running somewhere to get it work.
Take a look at the [molecule tests](./molecule/default/converge.yml) tests and the [default variables](./defaults/main.yml)

Dependencies
------------

[robertdebock.fail2ban](https://github.com/robertdebock/ansible-role-fail2ban)

License
-------

[Apache-2](https://www.apache.org/licenses/LICENSE-2.0)

Author Information
------------------

* Twitter [@tcharl](https://twitter.com/Tcharl)
* Github [@tcharl](https://github.com/Tcharl)
* LinkedIn [Charlie Mordant](https://www.linkedin.com/in/charlie-mordant-51796a97/)
