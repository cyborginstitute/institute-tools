import os.path

from utils.shell import command
from utils.config import lazy_config, AttributeDict
from utils.serialization import ingest_yaml_list

from fabric.api import task

@task
def deploy(target, conf=None):
    conf = lazy_config(conf)

    pconf = ingest_yaml_list(os.path.join(conf.paths.projectroot,
                                           conf.paths.builddata, 'deploy.yaml'))

    task_exists = False
    for task in pconf:
        if task['target'] == target:
            pconf = AttributeDict(task)
            task_exists = True
            break

    if task_exists is False:
        raise Exception('no deploy task named {0}'.format(target))

    cmd = 'rsync -raz {local_path}/ {username}@{remote_host}:{remote_path}'

    args = {
            'local_path': os.path.join(conf.paths.projectroot, conf.paths.output, pconf.paths.local),
            'username': pconf.host.username,
            'remote_host': pconf.host.hostname,
            'remote_path': pconf.paths.remote
           }


    command(cmd.format(**args))
    print('[deploy]: competed deploy of {0} to {1}'.format(pconf.target,
                                                           pconf.paths.remote))
