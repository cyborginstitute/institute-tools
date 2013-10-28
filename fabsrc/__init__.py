from fabric.api import puts, task
from utils.config import get_conf
import json

@task
def conf(conf=None):
    if conf is None:
        conf = get_conf()
    puts(json.dumps(conf, indent=3))
