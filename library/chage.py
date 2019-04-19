#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>, and others
# (c) 2016, Toshio Kuratomi <tkuratomi@ansible.com>
# (c) 2019, Evan Van Dam <evandam92@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: chage
short_description: Set expiry attributes on a user
version_added: historical
options:
  user:
    description:
      - The user to manage expiry attributes for.
    required: true
    default: null
  password_last_changed:
    description:
      - The date that the users password was last changed.
    required: no
    default: null
[...]
'''

EXAMPLES = '''
[...]
'''

from datetime import datetime
from ansible.module_utils.basic import AnsibleModule


CHAGE_DATE_FORMAT = '%b %d, %Y'


def run_chage(module, user, **kwargs):
    param_map = {
        'last_day': '--lastday',
        'expire_date': '--expiredate',
        'inactive': '--inactive',
        'min_days': '--mindays',
        'max_days': '--maxdays',
        'warn_days': '--warndays',
    }
    chage_args = ['chage', user]
    for key, val in kwargs:
        if val is not None:
            chage_args += [param_map[key], val]
    module.run_command(chage_args, check_rc=True)    


def check_chage(module, user, target_vals):
    """Check if the chage values match the target values"""
    rc, out, err = module.run_command(['chage', '-l', user], check_rc=True)
    pairs = (x.split(':') for x in out.strip().split('\n'))
    vals = dict((k.strip(), v.strip()) for k, v in pairs)

    def _parse_chage_date(d):
        if d == 'never':
            return -1
        return datetime.strptime(d, CHAGE_DATE_FORMAT)

    chage = dict(
        last_password_change=_parse_chage_date(vals['Last password change']),
        password_expire=_parse_chage_date(vals['Password expires']),
        password_inactive=_parse_chage_date(vals['Password inactive']),
        account_expire=_parse_chage_date(vals['Account expires']),
        min_days=int(vals['Minimum number of days between password change']),
        max_days=int(vals['Maximum number of days between password change']),
        warn_days=int(vals['Number of days of warning before password expires']),
    )

    return all([
        target_vals['last_day'] is None or chage['last_password_change'] == target_vals['last_day'],
        target_vals['expire_date'] is None or chage['account_expire'] == target_vals['expire_date'],
        target_vals['min_days'] is None or chage['min_days'] == target_vals['min_days'],
        target_vals['max_days'] is None or chage['max_days'] == target_vals['max_days'],
        target_vals['warn_days'] is None or chage['warn_days'] == target_vals['warn_days'],
    ])



def run_module():
    """Run the Ansible module"""
    def datetype(d):
        if d in (-1, 'never'):
            return -1
        return datetime.strptime(d, '%Y-%m-%d').date()

    module_args = dict(
        user=dict(required=True),
        last_day=dict(required=False, type=datetype),
        expire_date=dict(required=False, type=datetype),
        inactive=dict(required=False,),
        min_days=dict(required=False, type=int),
        max_days=dict(required=False, type=int),
        warn_days=dict(required=False, type=int),
    )

    result = dict(
        changed=False,
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    needs_change = check_chage(module, module.args)

    if needs_change:
        result['changed'] = True
        if not module.check_mode:
            run_chage(module, module.args)


def _main():
    run_module()


if __name__ == '__main__':
    _main()