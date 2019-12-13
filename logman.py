import time

LOG_PATH = './log.txt'

def log(text):
    print(text)
    with open(LOG_PATH, 'a') as fout:
        fout.write(time.ctime() + ' -- ' + text + '\n')

def clear_log():
    open(LOG_PATH, 'w').close()
