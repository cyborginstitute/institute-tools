import re
import os.path
import operator
from itertools import groupby

from utils.files import expand_tree
from utils.config import lazy_config, ingest_yaml_doc
from utils.grep import grep

def include_files(conf=None):
    conf = lazy_config(conf)

    source_dir = os.path.join(conf.paths.projectroot, conf.paths.source)

    inc_re = re.compile(r'\.\. include:: /(.*)')

    matches = grep(inc_re, expand_tree(source_dir, None))

    def tuple_sort(k):
        return k[1]
    matches.sort(key=tuple_sort)

    files = dict()

    for i in groupby(matches, operator.itemgetter(1)):
        files[i[0]] = set()
        for src in i[1]:
            if not src[0].endswith('~'):
                files[i[0]].add(src[0])
        files[i[0]] = list(files[i[0]])

    files.update(generated_includes(conf))

    return files


def generated_includes(conf=None):
    conf = lazy_config(conf)

    toc_spec_files = []
    step_files = []
    for fn in expand_tree(os.path.join(conf.paths.includes)):
        base = os.path.basename(fn)

        if base.startswith('toc-spec'):
            toc_spec_files.append(fn)
        elif base.startswith('ref-spec'):
            toc_spec_files.append(fn)
        elif base.startswith('steps'):
            step_files.append(fn)

    maskl = len(conf.paths.source)
    path_prefix = conf.paths.includes[maskl:]
    mapping = {}
    for spec_file in toc_spec_files:
        data = ingest_yaml_doc(spec_file)
        deps = [os.path.join(path_prefix, i) for i in data['sources']]

        mapping[spec_file[maskl:]] = deps

    for step_def in step_files:
        data = ingest_yaml_list(step_def)

        deps = []
        for step in data:
            if 'source' in step:
                deps.append(step['source']['file'])

        if len(deps) != 0:
            deps = [os.path.join(path_prefix, i) for i in deps]

            mapping[step_def[maskl:]] = deps

    return mapping


def include_files_unused(conf=None):
    conf = lazy_config(conf)

    inc_files = [fn[6:]
                 for fn in expand_tree(os.path.join(conf.paths.includes), None)]
    mapping = include_files(conf)

    results = []
    for fn in inc_files:
        if fn.endswith('yaml') or fn.endswith('~'):
            continue
        if fn not in mapping.keys():
            results.append(fn)

    return results


def included_once():
    results = []
    for file, includes in include_files().items():
        if len(includes) == 1:
            results.append(file)
    return results


def included_recusively():
    files = include_files()
    # included_files is a py2ism, depends on it being an actual list
    included_files = files.keys()

    results = {}
    for inc, srcs in files.items():
        for src in srcs:
            if src in included_files:
                results[inc] = srcs
                break

    return results


def includes_masked(mask):
    files = include_files()

    results = {}
    try:
        m = mask + '.rst'
        results[m] = files[m]
    except (ValueError, KeyError):
        for pair in files.items():
            if pair[0].startswith(mask):
                results[pair[0]] = pair[1]

    return results
