import os.path

from utils.shell import command
from utils.pdf import pdf_jobs
from utils.files import expand_tree, copy_if_needed
from utils.serialization import ingest_yaml_list
from jobs import runner

def build_pdfs(conf):
    regexes = [ ( re.compile(r'(index|bfcode)\{(.*)--(.*)\}'),
                  r'\1\{\2-\{-\}\3\}'),
                ( re.compile(r'\\PYGZsq{}'), "'"),
                ( re.compile(r'\\code\{/(?!.*{}/|etc|usr|data|var|srv)'),
                  r'\code{' + conf.project.url + r'/' + conf.project.tag) ]

    pdf_processor(conf=conf, regexes=regexes)

def build_sffms(conf):
    munge_script = os.path.join(conf.paths.buildsystem, 'bin', 'sffms-cleanup')

    base_dir = os.path.join(conf.paths.projectroot, conf.paths.output, 'sffms')

    preprocess = [ { 'job': command, 'args': [' '.join([munge_script, fn])] }
                   for fn in expand_tree(base_dir, 'tex') ]

    pdfs = ingest_yaml_list(os.path.join(conf.paths.builddata, 'pdfs.yaml'))

    count = runner(preprocess)
    print("[pdf] [sffms]: prepossessed {0} sffms files".format(count ))

    for pdf in pdfs:
        copy_if_needed(source_file=os.path.join(base_dir, pdf['input']),
                       target_file=os.path.join(base_dir, pdf['output']),
                       name='sffms')

    pdf_processor(conf, pdfs, None)

def pdf_processor(conf, pdfs, regexes):
    it = 0

    for queue in pdf_jobs(conf, pdfs, regexes):
        it += 1
        count = runner(queue)
        print("[pdf]: completed {0} pdf jobs, in stage {1}".format(count, it))
