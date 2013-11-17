import sys
import re
import os
import pkg_resources
import itertools
from multiprocessing import cpu_count

from fabric.api import task, abort, local, runs_once

from utils.config import lazy_config, BuildConfiguration, get_conf
from utils.files import create_link, copy_if_needed
from utils.archives import tarball
from utils.data import timestamp
from utils.jobs import dump_file_hashes

from utils.shell import command, build_platform_notification

from dependencies import refresh_dependencies
from jobs import runner
from pdf import build_pdfs

def get_sphinx_args(tag):
    if pkg_resources.get_distribution("sphinx").version.startswith('1.2b3'):
        return '-j ' + str(cpu_count() + 1) + ' '
    else:
        return ''

def prereq(sconf, conf=None):
    conf = lazy_config(conf)

    jobs = itertools.chain()

    job_count = runner(jobs)
    print('[sphinx]: processed {0} build prerequisite jobs'.format(job_count))

    generate_source(sconf, conf)
    dep_count = refresh_dependencies(conf)
    print('[sphinx]: refreshed {0} dependencies'.format(dep_count))

    command(build_platform_notification('Sphinx',
            'Build in progress past critical phase.'))

    dump_file_hashes(conf.system.dependency_cache, conf)

def generate_source(sconf, conf=None):
    conf = lazy_config(conf)

    target = sconf.build_source

    if not os.path.exists(target):
        os.makedirs(target)
        print('[sphinx-prep]: created ' + target)
    elif not os.path.isdir(sconf.build_source):
        abort('[sphinx-prep]: {0} exists and is not a directory'.format(target))

    r = command('rsync --checksum --recursive --delete {0}/ {1}'.format(sconf.source, target), capture=True)
    print('[sphinx]: updated source in {0}'.format(target))


@task
def build(*targets):
    conf = get_conf()

    sconf = BuildConfiguration(filename='sphinx.yaml',
                               directory=os.path.join(conf.paths.projectroot,
                                                      conf.paths.builddata))

    target_overrides = []
    std_sconf = None

    for target in targets:
        if target not in sconf:
            abort('[sphinx] [ERROR]: {0} is not a supported builder'.format(target))

        if 'config' in sconf[target]:
            target_overrides.append(target)

            sconf[target].target = sconf[target].config.builder
            sconf[target].source = os.path.join(conf.paths.projectroot,
                                              sconf[target].config.source)
            sconf[target].root = os.path.join(conf.paths.projectroot,
                                              conf.paths.output,
                                              sconf[target].config.tag)
            sconf[target].build_source = os.path.join(sconf[target].root,
                                                      conf.paths.source)
        else:
            sconf[target].target = target
            sconf[target].source = os.path.join(conf.paths.projectroot,
                                                conf.paths.source)
            sconf[target].root = os.path.join(conf.paths.projectroot,
                                              conf.paths.output)

            sconf[target].build_source = os.path.join(sconf[target].root,
                                                      'source')
            if std_sconf is None:
                std_sconf = sconf[target]

    if len(target_overrides) > 0:
        for tg in target_overrides:
            prereq(sconf[tg], conf)

    if std_sconf is not None:
        prereq(std_sconf, conf)

    if len(targets) <= 1:
        sphinx_build_worker(targets[0], conf, sconf)
    else:
        jobs = [{ 'job': sphinx_build_worker, 'args': [t, conf, sconf] }
                for t in targets ]
        runner(jobs, retval=None)

def sphinx_build_worker(target, conf, sconf, do_post=True):
    sconf = sconf[target]

    dirpath = os.path.join(sconf.root, target)
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)
        print('[{0}]: created {1}/{0}'.format(target, sconf.root))

    print('[sphinx] [{0}]: starting build at {1}'.format(target, timestamp()))

    tags = ' '.join(['-t ' + i for i in sconf.tags])
    cmd = 'sphinx-build -b {builder} {tags} -q -d {root}/doctrees-{builder} -c {config_path} {sphinx_args} {source} {root}/{builder}'

    sphinx_cmd = cmd.format(builder=sconf.target,
                            tags=tags,
                            root=sconf.root,
                            config_path=conf.paths.projectroot,
                            sphinx_args=get_sphinx_args(sconf.tags),
                            source=sconf.source
        )

    out = command(sphinx_cmd, capture=True)
    output_sphinx_stream('\n'.join([out.err, out.out]), target, conf)

    print('[sphinx] [{0}]: completed build at {1}'.format(target, timestamp()))

    finalize(target, sconf, conf)

def output_sphinx_stream(out, builder, conf=None):
    conf = lazy_config(conf)

    out = out.split('\n')
    out = list(set(out))

    out.sort()

    regx = re.compile(r'(.*):[0-9]+: WARNING: duplicate object description of ".*", other instance in (.*)')
    for l in out:
        if l == '':
            continue

        if builder.startswith('epub'):
            if l.startswith('WARNING: unknown mimetype'):
                continue
            elif len(l) == 0:
                continue
            elif l.startswith('WARNING: search index'):
                continue

        full_path = os.path.join(conf.paths.projectroot, conf.paths.output)
        if l.startswith(conf.paths.output):
            l = l[len(conf.paths.output)+1:]
        elif l.startswith(full_path):
            l = l[len(full_path)+1:]

        f1 = regx.match(l)
        if f1 is not None:
            g = f1.groups()

            if g[1].endswith(g[0]):
                continue

        l = os.path.join(conf.paths.projectroot, l)

        print(l)

def finalize(target, sconf, conf):
    jobs = {
        'html': [
            {'job': html_tarball,
             'args': [conf]
             },
        ],
        'dirhtml': [
            {'job': dirhtml_migration,
             'args': [conf]
            },
        ],
        'latex': [
            {'job': build_pdfs,
             'args': [conf]
            }
        ],
        'all': [],
    }


    if 'sitemap_config' in sconf:
        jobs[target].append({'job': sitemap,
                             'args': [os.path.join(conf.paths.projectroot,
                                                   sconf.sitemap_config)]
                             })

    if target not in jobs:
        jobs[target] = []

    print('[sphinx] [post] [{0}]: running post-processing steps.'.format(target))
    count = runner(itertools.chain(jobs[target], jobs['all']))
    print('[sphinx] [post] [{0}]: completed {1} post-processing steps'.format(target, count))

def dirhtml_migration(conf):
    cmd = 'rsync -a {source}/ {destination}'
    command(cmd.format(source=os.path.join(conf.paths.projectroot,
                                           conf.paths.output, 'dirhtml'),
                       destination=os.path.join(conf.paths.projectroot,
                                                conf.paths.public)))

def html_tarball(conf):
    release_fn = os.path.join(conf.paths.projectroot,
                              conf.paths.output,
                              'html', 'release.txt')

    with open(release_fn, 'w') as f:
        f.write(conf.git.commit)

    basename = os.path.join(conf.paths.projectroot,
                            conf.paths.public,
                            conf.project.name + '-' + conf.git.branches.current)

    tarball_name = basename + '.tar.gz'

    tarball(name=tarball_name,
            path='html',
            cdir=os.path.join(conf.paths.projectroot,
                              conf.paths.output),
            sourcep='html',
            newp=os.path.basename(basename))

    create_link(input_fn=os.path.basename(tarball_name),
                output_fn=os.path.join(conf.paths.projectroot,
                                       conf.paths.public,
                                       conf.project.name + '.tar.gz'))


def sitemap(config_path=None, conf=None):
    conf = lazy_config(conf)

    sys.path.append(
        os.path.join(conf.paths.projectroot, conf.paths.buildsystem, 'vendor'))
    import sitemap_gen

    if not os.path.exists(config_path):
        print('[ERROR] [sitemap]: configuration file {0} does not exist. Returning early'.format(config_path))
        return False

    sitemap = sitemap_gen.CreateSitemapFromFile(configpath=config_path,
                                                suppress_notify=True)
    if sitemap is None:
        print('[ERROR] [sitemap]: failed to generate the sitemap due to encountered errors.')
        return False

    sitemap.Generate()

    print('[sitemap]: generated sitemap according to the config file {0}'.format(config_path))
    return True
