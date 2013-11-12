from utils.pdf import pdf_jobs
from jobs import runner

def build_pdfs(conf):
    it = 0
    for queue in pdf_jobs(conf):
        it += 1
        count = runner(queue)
        print("[pdf]: completed {0} pdf jobs, in stage {1}".format(count, it))
