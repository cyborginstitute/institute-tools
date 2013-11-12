import os
import re
import subprocess

from config import lazy_config
from serialization import ingest_yaml_list
from files import copy_if_needed

def munge_tex(fn, regexes):
    with open(fn, 'r') as f:
        tex = f.read()

    for regex, subst in regexes:
        tex = regex.sub(subst, tex)

    with open(fn, 'w') as f:
        f.write(tex)

    print('[pdf]: processed Sphinx latex format for {0}'.format(fn))

def render_tex_into_pdf(fn, path):
    pdflatex = 'TEXINPUTS=".:{0}:" pdflatex --interaction batchmode --output-directory {0} {1}'.format(path, fn)

    try:
        with open(os.devnull, 'w') as f:
            subprocess.check_call(pdflatex, shell=True, stdout=f, stderr=f)
    except subprocess.CalledProcessError:
        print('[ERROR]: {0} file has errors, regenerate and try again'.format(fn))
        return False

    print('[pdf]: completed pdf rendering stage 1 of 4 for: {0}'.format(fn))

    try:
        with open(os.devnull, 'w') as f:
            subprocess.check_call("makeindex -s {0}/python.ist {0}/{1}.idx ".format(path, os.path.basename(fn)[:-4]), shell=True, stdout=f, stderr=f)
    except subprocess.CalledProcessError:
        print('[ERROR]: {0} file has errors, regenerate and try again'.format(fn))
    print('[pdf]: completed pdf rendering stage 2 of 4 (indexing) for: {0}'.format(fn))

    try:
        with open(os.devnull, 'w') as f:
            subprocess.check_call(pdflatex, shell=True, stdout=f, stderr=f)
    except subprocess.CalledProcessError:
        print('[ERROR]: {0} file has errors, regenerate and try again'.format(fn))
        return False
    print('[pdf]: completed pdf rendering stage 3 of 4 for: {0}'.format(fn))

    try:
        with open(os.devnull, 'w') as f:
            subprocess.check_call(pdflatex, shell=True, stdout=f, stderr=f)
    except subprocess.CalledProcessError:
        print('[ERROR]: {0} file has errors, regenerate and try again'.format(fn))
        return False
    print('[pdf]: completed pdf rendering stage 4 of 4 for: {0}'.format(fn))

    print('[pdf]: rendered {0}.{1}'.format(os.path.basename(fn), 'pdf'))


def pdf_jobs(conf):
    conf = lazy_config(conf)

    pdfs = ingest_yaml_list(os.path.join(conf.paths.builddata, 'pdfs.yaml'))
    tex_regexes = [ ( re.compile(r'(index|bfcode)\{(.*)--(.*)\}'),
                      r'\1\{\2-\{-\}\3\}'),
                    ( re.compile(r'\\PYGZsq{}'), "'"),
                    ( re.compile(r'\\code\{/(?!.*{}/|etc|usr|data|var|srv)'),
                      r'\code{' + conf.project.url + r'/' + conf.project.tag) ]

    # this is temporary
    queue = ( [], [], [], [] )

    for i in pdfs:
        tagged_name = i['output'][:-4]
        deploy_fn = tagged_name + '-' + conf.git.branches.current + '.pdf'
        deploy_path = conf.paths.public
        latex_dir = os.path.join(conf.paths.output, 'latex')

        i['source'] = os.path.join(latex_dir, i['output'])
        i['processed'] = os.path.join(latex_dir, tagged_name + '.tex')
        i['pdf'] = os.path.join(latex_dir, tagged_name + '.pdf')
        i['deployed'] = os.path.join(deploy_path, deploy_fn)
        i['path'] = latex_dir

        # these appends will become yields, once runner() can be dependency
        # aware.
        queue[0].append(dict(dependency=None,
                             target=i['source'],
                             job=munge_tex,
                             args=(i['source'], tex_regexes)))

        queue[1].append(dict(dependency=i['source'],
                             target=i['processed'],
                             job=copy_if_needed,
                             args=(i['source'], i['processed'], 'pdf')))

        queue[2].append(dict(dependency=i['processed'],
                             target=i['pdf'],
                             job=render_tex_into_pdf,
                             args=(i['processed'], i['path'])))

        queue[3].append(dict(dependency=i['pdf'],
                             target=i['deployed'],
                             job=copy_if_needed,
                             args=(i['pdf'], i['deployed'], 'pdf')))

    return queue
