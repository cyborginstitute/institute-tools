import json
import os.path

from fabric.api import task
from fabric.utils import puts

from docs_meta import get_conf

from stats.reports import generate_report, lazy_data, aggregated_report
from stats.includes import (include_files, included_recusively, included_once,
                            include_files_unused, generated_includes, includes_masked)

# user facing operations ##########
# User facing fabric tasks


@task
def wc(mask=None):
    report = generate_report(mask)

    count = 0
    for doc in report:
        count += doc['stats']['word-count']

    msg = "[stats]: there are {0} words".format(count)
    if mask is None:
        msg += ' total'
    else:
        msg += ' in ' + mask

    puts(msg)

    return count


@task
def report(fn=None):
    data = generate_report(fn)
    if len(data) > 1:
        data.append(multi(fn, data, None))

    puts(json.dumps(data, indent=3))


@task
def output_report(mask, filename, conf=None, data=None):
    output = generate_report(mask, filename, data, conf)

    if filename == 'print':
        puts(json.dumps(output, indent=2))
    else:
        with open(filename, 'w') as f:
            json.dump(output, f)


@task
def multi(mask=None, data=None, output_file='print'):
    data = lazy_data(mask, data)

    o = aggregated_report(mask, data)

    if output_file is None:
        return o
    elif output_file == 'print':
        puts(json.dumps(o, indent=3, sort_keys=True))
    else:
        json.dump(o, output_file, indent=3)


@task
def includes(mask='all'):
    if mask == 'list':
        results = include_files().keys()
    elif mask == 'all':
        results = include_files()
    elif mask.startswith('rec'):
        results = included_recusively()
    elif mask == 'single':
        results = included_once()
    elif mask == 'unused':
        results = include_files_unused()
    elif mask.startswith('gen'):
        results = generated_includes()
    else:
        if mask.startswith('source'):
            mask = mask[6:]
        if mask.startswith('/source'):
            mask = mask[7:]

        results = includes_masked(mask)

    puts(json.dumps(results, indent=3))


@task
def changed(output='print'):
    try:
        from pygit2 import Repository, GIT_STATUS_CURRENT, GIT_STATUS_IGNORED
    except ImportError:
        puts('[stats]: cannot detect changed files. Please install pygit2')

    conf = get_conf()

    repo_path = conf.paths.projectroot

    r = Repository(repo_path)

    changed = []
    for path, flag in r.status().items():
        if flag not in [GIT_STATUS_CURRENT, GIT_STATUS_IGNORED]:
            if path.startswith(conf.paths.source):
                if path.endswith('.txt'):
                    changed.append(path[6:])

    source_path = os.path.join(
        conf.paths.source, conf.paths.output, conf.git.branches.current, 'json')
    changed_report = []

    for report in generate_report(None):
        if report['source'][len(source_path):] in changed:
            changed_report.append(report)

    if not len(changed_report) == 0:
        changed_report.append(multi(data=changed_report, output_file=None))

    if output is None:
        return changed_report
    elif output == 'print':
        puts(json.dumps(changed_report, indent=2))
    else:
        json.dump(changed_report, output)
