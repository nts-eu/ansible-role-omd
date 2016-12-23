#!/usr/bin/python

# Copyright (c) 2016, Markus Rainer <markus.rainer@nts.eu>
#
# All rights reserved.
#
# License: Apache 2.0
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
# * Neither the name of the Juniper Networks nor the
#   names of its contributors may be used to endorse or promote products
#   derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY Juniper Networks, Inc. ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL Juniper Networks, Inc. BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


from ansible.module_utils.basic import *
import re

def _stop_omd(module, site):
	return module.run_command('omd stop ' + site)

def _get_value(module, site, key):
	return module.run_command('omd config ' + site + ' show ' + key)

def _set_value(module, site, key, value):
	return module.run_command('omd config ' + site + ' set ' + key + " " + value)

def main():

	module = AnsibleModule(
		argument_spec=dict(
			site=dict(required=True),
			key=dict(required=True),
			value=dict(required=True),
		)
	)

	site = module.params['site']
	key = module.params['key']
	value = module.params['value']

	getv = _get_value(module, site, key)
	if len(getv) < 2:
		module.fail_json(msg="wrong output from 'omd get config'")

	if (re.match(getv[1].rstrip(), 'No such variable.*')):
		module.fail_json(msg="no such variable: " + key)

	if (re.match(getv[1].rstrip(), value)): 
		module.exit_json(changed=False, meta=getv)

	stopv = _stop_omd(module, site)
	if (stopv[0] != 0):
		module.fail_json(msg="can't stop omd service: " + stopv[1])

	setv = _set_value(module, site, key, value)
	if (setv[0] != 0):
		module.fail_json(msg="can't set omd config: " + setv[1])

	getv = _get_value(module, site, key)
	if (getv[0] == 0 and re.match(getv[1].rstrip(), value)): 
		module.exit_json(changed=True, meta={key:value})
	else: 
		module.fail_json(msg=setv)

if __name__ == '__main__':
	main()
