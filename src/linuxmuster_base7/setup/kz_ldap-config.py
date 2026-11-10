#!/usr/bin/python3
#
# write the ldap configuration used by linuxmuster-tools7
# lukas.spitznagel@netzint.de
# 20261110
#

"""Setup module kz_ldap-config: write /etc/linuxmuster/tools/ldap.yml.

linuxmusterTools/ldapconnector/connector.py reads the LDAP search base from
its own config file. Only linuxmuster-base7 knows the values: the base DN and
the server name come out of setup.ini, and the global-binduser password is
created one step earlier, by k_samba-users.

The schema is owned and documented by linuxmuster-tools7
(linuxmusterTools/ldapconnector/README.md); this step only fills it in. That
is also why nothing here reads the file back: tools7 defines what the keys
mean, base7 supplies the values.

Upstream this file was /etc/linuxmuster/webui/config.yml and was created by
linuxmuster-webui7, which this fork does not install.

Sorts after k_samba-users on purpose - every digit sorts before '_', so a
name like k2_... would run *before* it and find no binduser secret.
"""

import os
import sys
sys.path.insert(0, '/usr/lib/linuxmuster')
import environment

from linuxmuster_base7.functions import getSetupValue, mySetupLogfile, printScript
from linuxmuster_base7.functions import readTextfile, writeSecretFile

logfile = mySetupLogfile(__file__)

CONFIGDIR = '/etc/linuxmuster/tools'
CONFIGFILE = CONFIGDIR + '/ldap.yml'


def yamlScalar(value):
    """Quote a value so that YAML reads it back as the string it is.

    randomPassword() produces letters and digits only, so an all-digit
    password is possible - unquoted, yaml would hand it back as an int.
    """
    return '"' + str(value).replace('\\', '\\\\').replace('"', '\\"') + '"'


msg = 'Writing ldap configuration '
printScript(msg, '', False, False, True)
try:
    basedn = getSetupValue('basedn')
    servername = getSetupValue('servername')
    if not basedn or not servername:
        raise Exception('basedn or servername missing in ' + environment.SETUPINI)

    rc, bindpw = readTextfile(environment.BINDUSERSECRET)
    if not rc:
        raise Exception('Cannot read ' + environment.BINDUSERSECRET)
    bindpw = bindpw.strip()

    binddn = 'CN=global-binduser,OU=Management,OU=GLOBAL,' + basedn

    # Written by hand rather than with a yaml dump: four scalars do not
    # justify a dependency on python3-yaml in this package.
    content = ('# Written by linuxmuster-setup (kz_ldap-config).\n'
               '# Schema: linuxmusterTools/ldapconnector/README.md\n'
               'binddn: ' + yamlScalar(binddn) + '\n'
               'bindpw: ' + yamlScalar(bindpw) + '\n'
               'host: ' + yamlScalar(servername) + '\n'
               'searchdn: ' + yamlScalar(basedn) + '\n')

    os.makedirs(CONFIGDIR, mode=0o755, exist_ok=True)
    # Carries the binduser password, so it is written like the other secrets.
    if not writeSecretFile(CONFIGFILE, content, 0o600):
        raise Exception('Cannot write ' + CONFIGFILE)

    printScript(' Success!', '', True, True, False, len(msg))
except Exception as error:
    printScript(f' Failed: {error}', '', True, True, False, len(msg))
    sys.exit(1)
