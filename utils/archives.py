import os
import sys

from fabric.api import local, settings, puts

def _get_gnutar_cmd():
    if sys.platform in ['linux', 'linux2']:
        return '/bin/tar'
    elif sys.platform == 'darwin':
        return '/usr/bin/gnutar'
    else:
        return 'tar'

def tarball(name, path, sourcep=None, newp=None, cdir=None):
    cmd = [ _get_gnutar_cmd() ]

    if cdir is not None:
        if not cdir.endswith('/'):
            cdir = cdir + '/'

        cmd.extend([ '-C', cdir ])

    if not os.path.exists(os.path.dirname(name)):
        os.makedirs(os.path.dirname(name))

    if sourcep is not None and newp is not None:
        cmd.append('--transform=s/{0}/{1}/'.format(sourcep, newp))

    cmd.extend(['-czf', name, './' + path])

    with settings(host_string='tarball'):
        local(' '.join(cmd), capture=False)

    puts('[tarball]: created {0}'.format(name))
