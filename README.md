# Ansible Role: ansible-role-omd
Ansible Role for OMD (Ubuntu and Debian)

========

Install and Configure OMD - The Open Monitoring Distribution
Tested on Ubuntu. Should work for Debian

Requirements
-------

Ubuntu 16.04 Server

Role Variables
--------------

```
omd_feature_gearmand: false
omd_feature_nagios: false
omd_feature_worker: false
omd_feature_pnp4nagios: false

omd_gearmand_ip: false
omd_apt_name: omd-labs-edition-daily
omd_apt_repo: http://labs.consol.de/repo/testing/ubuntu

omd_site: central
omd_user_id: 10005
omd_group_id: 10005

omd_config_apache_tcp_port: 5000
omd_config_mod_gearman: "on"
omd_config_gearmand_port: 4730

omd_config_livestatus_tcp_port: 6557
omd_config_default_gui: thruk
omd_config_core: nagios
# len must be 32
omd_mod_gearman_key: false
```

License
-------

MIT

Author Information
------------------
Markus Rainer maxrainer18(at)gmail.com
