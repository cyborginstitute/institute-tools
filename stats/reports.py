import os.path
import json

from droopy.factory import DroopyFactory
from droopy.lang.english import English

from utils.config import lazy_config
from utils.jobs import runner
from utils.files import expand_tree

from weakness import Weakness


def lazy_data(mask, data):
    if data is None:
        return generate_report(mask)
    else:
        return data


def resolve_input_file(fn):
    if fn.startswith('/'):
        fn = fn[1:]
    if fn.startswith('source'):
        fn = fn[7:]

    base_fn = os.path.splitext(fn)[0]
    source = '.'.join([os.path.join('source', base_fn), 'txt'])

    return base_fn, source


def render_report(fn):
    with open(os.path.abspath(fn), 'r') as f:
        text = json.load(f)['text']

    base_fn, source = resolve_input_file(fn)

    droopy = DroopyFactory.create_full_droopy(text, English())
    droopy.add_bundles(Weakness())
    droopy.foggy_word_syllables = 3

    r = {
        'report': 'file',
        'file': fn,
        'source': source,
        'stats': {
            'weasels': {
                'count': droopy.weasel_count,
                'set': droopy.weasel_list
            },
            'passives': {
                'count': droopy.passive_count,
                'set': droopy.passive_list
            },
            'smog-index': droopy.smog,
            'flesch-level': droopy.flesch_grade_level,
            'flesch-ease': droopy.flesch_reading_ease,
            'coleman-liau': droopy.coleman_liau,
            'word-count': droopy.nof_words,
            'sentence-count': droopy.nof_sentences,
            'sentence-len-avg': droopy.nof_words / droopy.nof_sentences,
            'foggy': {
                'factor': droopy.foggy_factor,
                'count':  droopy.nof_foggy_words,
                'threshold':  droopy.foggy_word_syllables,
            },
        }
    }

    return r


def report_jobs(docs, mask):
    for doc in docs:
        if doc.endswith('searchindex.json') or doc.endswith('globalcontext.json'):
            continue
        elif mask is None:
            yield {
                'job': render_report,
                'args': dict(fn=doc),
                'target': None,
                'dependency': None
            }
        elif doc.startswith(mask):
            yield {
                'job': render_report,
                'args': [doc],
                'target': None,
                'dependency': None
            }

# Report Generator


def generate_report(mask, output_file=None, conf=None, data=None):
    conf = lazy_config(conf)

    base_path = os.path.join(
        conf.build.paths.output, conf.git.branches.current, 'json')

    if mask is not None:
        if mask.startswith('/'):
            mask = mask[1:]

        mask = os.path.join(base_path, mask)

    if data is None:
        docs = expand_tree(base_path, '.json')

        output = runner(jobs=report_jobs(docs, mask),
                        retval='results')
    else:
        output = data

    return output


def sum_key(key, data, sub=None):
    r = 0
    for d in data:
        if sub is not None:
            d = d[sub]

        try:
            r += d[key]
        except TypeError:
            r += d[key]['count']
    return r


def aggregated_report(mask, data):
    n = len(data)
    o = dict()

    keys = ["flesch-ease", "sentence-count", "word-count",
            "smog-index", "sentence-len-avg", "flesch-level",
            "coleman-liau", "passives", "foggy", "weasels"]

    for key in keys:
        o[key] = sum_key(key, data, 'stats')

    r = dict()
    for k, v in o.iteritems():
        r[k] = float(v) / n if n > 0 else float('nan')

    r['word-count'] = int(r['word-count'])
    r['sentence-len-avg'] = int(r['sentence-len-avg'])

    o = {'report': 'multi',
         'mask': mask if mask is not None else "all",
         'averages': r,
         'totals': {
             'passive': o['passives'],
             'foggy': o['foggy'],
             'weasel': o['weasels'],
             'word-count': o['word-count']
         }
         }

    return o
