from jobs import runner

def grep(regex, files):
    matches = runner( grep_jobs(regex, files), True, retval='results')

    return [m for match in matches for m in match] 

def grep_jobs(regex, files):
    for fn in files:
        yield {
            'job': grep_worker,
            'args': [regex, fn],
        }

def grep_worker(regex, fn):
    matches = []
    with open(fn, 'r') as f:
        for ln in f.readlines():
            m = regex.match(ln)
            if m is not None:
                matches.append((fn, m.group(1)))

    return matches
