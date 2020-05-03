Ansible SecureHost
=========

* Galaxy: [![Ansible Galaxy](https://img.shields.io/badge/galaxy-tcharl.ansible_securehost-660198.svg?style=flat)](https://galaxy.ansible.com/tcharl/ansible_securehost)
* Lint, Tests & requirements: ![Molecule](https://github.com/OsgiliathEnterprise/ansible-securehost/workflows/Molecule/badge.svg)
* Chat: [![Join the chat at https://gitter.im/OsgiliathEnterprise/platform](https://badges.gitter.im/OsgiliathEnterprise/platform.svg)](https://gitter.im/OsgiliathEnterprise/platform?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

Wrapper role on top of [robertdebock.fail2ban](https://github.com/robertdebock/ansible-role-fail2ban)
In addition, it will disable login/password ssh authentication 

Requirements
------------

Like any other platform role, executing `./configure`

Role Variables
--------------

Same as [robertdebock.fail2ban](https://github.com/robertdebock/ansible-role-fail2ban)

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
