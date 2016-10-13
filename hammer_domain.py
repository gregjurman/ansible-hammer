#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2016, Greg Jurman <jurman.greg@gmail.com>
#
# This file is part of Ansible
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: hammer_domain
short_description: Command foreman domain configuration
requirements: []
version_added: "0.1"
author: Greg Jurman (@gregjurman) <jurman.greg@gmail.com>
description:
  - This module allows running hammer tasks on a Foreman server.
notes:
  - This module requires foreman_username and foreman_password to be set
    in group_vars or host_vars else it will default to admin/admin.
options:
  domain:
    description:
      - "The domain to be created, modified, or removed from foreman"
    required: true
  state:
    description:
      - "The state the domain must be in"
    choices:
      - present -- Domain must be defined
      - absent -- Domain must not be defined
    default: present
  description:
    description:
      - "The description of the domain"
    required: false
  username:
    description:
      - "Username for authentication with Foreman"
    required: false
    default: "admin"
  password:
    description:
      - "Password for authentication with Foreman"
    required: false
    default: "admin"
  server:
    description:
      - "Hostname of Foreman server to communicate with"
    required: false
'''
EXAMPLES = '''
# Add new domain with defaults
- hammer_domain: domain=development.local state=present
  become: yes
'''


def append_param(cmd, param, flag):
    if param is not None:
        cmd.extend([flag, param])


def push_arguments(command='info'):
    cmd = ['hammer','--output', 'json', 'domain', command]
    return cmd


def append_domain(domain, module, params):
    cmd = push_arguments('create')
    append_param(cmd, params['name'], '--name')
    append_param(cmd, params['description'], '--description')
    append_param(cmd, params['proxy'], '--dns')
    append_param(cmd, params['proxy_id'], '--dns-id')
    module.run_command(cmd, check_rc=True)


def remove_domain(domain, module, params):
    cmd = push_arguments('delete')
    append_param(cmd, params['domain'], '--name')
    module.run_command(cmd, check_rc=True)
    pass


def check_present(domain, module, params):
    cmd = push_arguments('info')
    append_param(cmd, params['name'], '--name')
    ret, _, __ = module.run_command(cmd, check_rc=False)
    return (ret == 0)


def main():
    module = AnsibleModule(
        supports_check_mode=True,
        argument_spec=dict(
            name=dict(required=True, default=None, type='str'),
            state=dict(required=False, default='present',
                       choices=['present', 'absent']),
            server=dict(required=False, default=None, type='str'),
            username=dict(required=False, default='admin', type='str'),
            password=dict(required=False, default='admin', type='str'),
            description=dict(required=False, default=None, type='str'),
            proxy=dict(required=False, default=None, type='str'),
            proxy_id=dict(required=False, default=None, type='int'),
        ),
    )
    args = dict(
        changed=False,
        failed=False,
        name=module.params['name'],
        username=module.params['username'],
        password=module.params['password'],
        state=module.params['state'],
        description=module.params['description'],
        proxy=module.params['proxy'],
        proxy_id=module.params['proxy_id'],
        server=module.params['server']
    )

    module.run_command_environ_update = dict(
        FOREMAN_USERNAME=args['username'],
        FOREMAN_PASSWORD=args['password']
    )

    if args['server'] is not None:
        module.run_command_environ_update.update(
             dict(FOREMAN_SERVER=args['server']
        ))

    if args['proxy'] is not None and args['proxy_id'] is not None:
        module.fail_json(changed=False,
                         msg="Cannot have 'proxy' and 'proxy_id' set.")

    domain_is_present = check_present(args['name'], module, module.params)
    should_be_present = (args['state'] == 'present')

    # Check if target is up to date
    args['changed'] = (domain_is_present != should_be_present)

    # Check only; don't modify
    if module.check_mode:
        module.exit_json(changed=args['changed'])

    # Target is already up to date
    if args['changed'] == False:
        module.exit_json(**args)

    if should_be_present:
        append_domain(args['name'], module, module.params)
    else:
        remove_domain(args['name'], module, module.params)

    module.exit_json(**args)


# import module snippets
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
