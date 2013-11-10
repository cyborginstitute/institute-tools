import json
import os
import sys

from fabric.state import output
from fabric.api import puts, task

from utils.config import get_conf

output.status = False
output.aborts = True
output.warnings = True
output.running = False
output.user = True

import sphinx
import stats

from jobs import force, serial


@task
def conf(conf=None):
    if conf is None:
        conf = get_conf()
    puts(json.dumps(conf, indent=3))
