import json
import os.path

from serialization import ingest_yaml_doc
from git import get_branch, get_commit
from structures import AttributeDict

class BuildConfiguration(AttributeDict):
    def __init__(self, filename, directory=None):
        if directory is None:
            directory = os.path.split(os.path.abspath(filename))[0]

        if filename.endswith('yaml'):
            conf = ingest_yaml_doc(get_conf_file(filename, directory))
        elif filename.endswith('json'):
            with open(os.path.join(directory, filename), 'r') as f:
                conf = json.load(f)

        for key, value in conf.items():
            if isinstance(value, (list, tuple)):
                for item in value:
                    if isinstance(item, dict):
                        setattr(self, key, AttributeDict(item))
                    else:
                        setattr(self, key, value)
            else:
                if isinstance(value, dict):
                    setattr(self, key, AttributeDict(value))
                else:
                    setattr(self, key, value)

def conf_from_list(key, source):
    return AttributeDict(dict( (item[key], item) for item in source ))

def get_conf_file(file, directory=None):
    if directory is None:
        conf = get_conf()

        directory = conf.build.paths.builddata

    conf_file = os.path.split(file)[1].rsplit('.', 1)[0] + '.yaml'

    return os.path.join(directory, conf_file)

def load_conf(path=None):
    if path is None:
        try:
            project_root_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
            conf = BuildConfiguration(filename='conf.yaml',
                                      directory=os.path.join(project_root_dir, 'config'))
        except IOError:
            project_root_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
            conf = BuildConfiguration(filename='conf.yaml',
                                      directory=project_root_dir)
        except IOError:
            project_root_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
            conf = BuildConfiguration(filename='conf.yaml',
                                      directory=project_root_dir)
    else:
        try:
            project_root_dir = path
            conf = BuildConfiguration(filename='conf.yaml',
                                      directory=os.path.join(project_root_dir, 'config'))
        except IOError:
            project_root_dir = path
            conf = BuildConfiguration(filename='conf.yaml',
                                      directory=project_root_dir)
        except IOError:
            project_root_dir = path
            conf = BuildConfiguration(filename='conf.yaml',
                                      directory=os.path.join(project_root_dir, 'bin'))


    conf.paths.projectroot = project_root_dir
    return conf

def get_conf(path=None):
    conf = load_conf(path)

    conf['system'] = AttributeDict()
    if os.path.exists('/etc/arch-release'):
        conf.system.python = 'python2'
    else:
        conf.system.python = 'python'

    conf.git['branches']  = AttributeDict()
    conf.git.branches.current = get_branch()
    conf.git.commit = get_commit()

    conf.paths.update(render_paths(conf))

    conf.system.dependency_cache = os.path.join(conf.paths.projectroot,
                                                conf.paths.output,
                                                'dependencies.json')

    return conf

def lazy_config(conf):
    if conf is None:
        return get_conf()
    else:
        return conf

def render_paths(conf=None):
    if conf is None:
        conf = load_conf()

    paths = conf.paths

    paths.public = os.path.join(paths.output, 'public')
    paths.buildarchive = os.path.join(paths.output, 'archive')
    paths.includes = os.path.join(paths.source, 'includes')
    paths.buildsource = os.path.join(paths.output, 'source')

    return paths
