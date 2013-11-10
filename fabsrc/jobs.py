from multiprocessing import cpu_count

from fabric.api import env, task

from utils.jobs import sync_runner, async_runner

env.FORCE = False


@task
def force():
    env.FORCE = True

env.PARALLEL = True


@task
def serial():
    env.PARALLEL = False


def runner(jobs, pool=None, parallel=True, force=False, retval='count'):
    if pool == 1 or parallel is False:
        return sync_runner(jobs, force, retval)
    else:
        if pool is None:
            pool = cpu_count()

        return async_runner(jobs, force, pool, retval)
