import time

LOGFILE_PATH = '/tmp/waterman-log.txt'

def log(*args):
    text = time.ctime() + ' -- ' + ' '.join([str(e) for e in args])
    print(text)
    with open(LOGFILE_PATH, 'a') as fout:
        fout.write(text + '\n')

def clear_log():
    open(LOGFILE_PATH, 'w').close()

def dump():
    with open(LOGFILE_PATH) as f:
        return f.read()
