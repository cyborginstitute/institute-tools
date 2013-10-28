import json
import os.path

from serialization import ingest_yaml_doc
from git import get_branch, get_commit

class AttributeDict(dict):
    def __init__(self, value=None):
        if value is None:
            passu
        elif isinstance(value, dict):
            for key in value:
                self.__setitem__(key, value[key])
        else:
            raise TypeError('expected dict')

    def __setitem__(self, key, value):
        if isinstance(value, dict) and not isinstance(value, AttributeDict):
            value = AttributeDict(value)
        dict.__setitem__(self, key, value)

    def __getitem__(self, key):
        NotFound = object()
        found = self.get(key, NotFound)
        if found is NotFound:
            err = 'key named "{0}" does not exist.'.format(key)
            raise AttributeError(err)
        else:
            return found

    __setattr__ = __setitem__
    __getattr__ = __getitem__

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

def load_conf():
    try:
        project_root_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
        print(project_root_dir)
        conf = BuildConfiguration(filename='conf.yaml',
                                  directory=os.path.join(project_root_dir, 'bin'))
    except IOError:
        project_root_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
        print(project_root_dir)
        conf = BuildConfiguration(filename='conf.yaml',
                                  directory=os.path.join(project_root_dir, 'bin'))

    conf.paths.projectroot = project_root_dir

def get_conf():
    conf = load_conf()

    if os.path.exists('/etc/arch-release'):
        conf.system.python = 'python2'
    else:
        conf.system.python = 'python'

    conf.git.branches.current = get_branch()
    conf.git.commit = get_commit()

    conf.paths.update(render_paths('dict'), conf)

    return conf

def render_paths(fn=None, conf=None):
    if conf is None:
        conf = load_conf()

    paths = conf.paths

    paths.public = os.path.join(paths.output, 'public')
    paths.buildarchive = os.path.join(paths.output, 'archive')

    return paths
