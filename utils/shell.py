import os
import sys
import re
import subprocess
from structures import AttributeDict

def shell_value(args, path=None):
    if path is None:
        path = os.getcwd()

    if isinstance(args , str):
        r = re.compile("\s+")
        args = r.split(args)

    p = subprocess.Popen(args, cwd=path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    r = p.communicate()

    return str(r[0].decode().rstrip())

class CommandError(Exception): pass

def command(command, capture=False, ignore=False):
    dev_null = None
    if capture:
        out_stream = subprocess.PIPE
        err_stream = subprocess.PIPE
    else:
        dev_null = open(os.devnull, 'w+')
        # Non-captured, hidden streams are discarded.
        out_stream = dev_null
        err_stream = dev_null
    try:
        p = subprocess.Popen(command, shell=True, stdout=out_stream,
                             stderr=err_stream)

        (stdout, stderr) = p.communicate()
    finally:
        if dev_null is not None:
            dev_null.close()

    out = {
        'cmd': command,
        'err': stderr.strip() if stdout else "",
        'out': stdout.strip() if stdout else "",
        'return_code': p.returncode,
        'succeeded': True if p.returncode == 0 else False,
        'failed': False if p.returncode == 0 else True
    }

    out = AttributeDict(out)

    if ignore is True:
        return out
    elif out.succeeded is True:
        if capture is True:
            return out
        else:
            return None
    else:
        print('[ERROR]: ' + out.cmd)
        print('[ERROR]: returned ' + out.return_code)
        raise CommandError

def build_platform_notification(title, content):
    if sys.platform.startswith('darwin'):
        return 'growlnotify -n "mongodb-doc-build" -a "Terminal.app" -m %s -t %s' % (title, content)
    if sys.platform.startswith('linux'):
        return 'notify-send "%s" "%s"' % (title, content)
