import os
import json


from utils.config import lazy_config
from utils.jobs import runner, check_hashed_dependency

from stats.includes import include_files


def update_dependency(fn):
    if os.path.exists(fn):
        os.utime(fn, None)


def refresh_dependency_jobs(conf=None):
    conf = lazy_config(conf)
    graph = include_files(conf)

    if not os.path.exists(conf.system.dependency_cache):
        dep_map = None
    else:
        with open(conf.system.dependency_cache, 'r') as f:
            dep_cache = json.load(f)
            dep_map = dep_cache['files']

    for target, deps in graph.items():
        yield {
            'job': dep_refresh_worker,
            'args': [target, deps, dep_map, conf],
            'target': None,
            'dependency': None
        }


def dep_refresh_worker(target, deps, dep_map, conf):
    if check_hashed_dependency(target, deps, dep_map) is True:
        target = os.path.join(conf.paths.projectroot,
                              conf.paths.buildsource,
                              target[1:])

        update_dependency(target)

        return 1
    else:
        return 0


def refresh_dependencies(conf=None):
    conf = lazy_config(conf)

    return sum(runner(refresh_dependency_jobs(conf), retval='results'))
