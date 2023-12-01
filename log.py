import logging

def getlogger(level=logging.DEBUG,format="%(asctime)s %(name)s %(levelname)s %(message)s",dateformat='%Y-%m-%d  %H:%M:%S %a ',logfile="log.txt"):
    mylog = logging.RootLogger(level)  # logging.Logger(name='my',level='INFO')
    if format:
        LOG_FORMAT=format
    if dateformat:
        DATE_FORMAT=dateformat
    if logfile:
        LOG_FILE=logfile
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    fh = logging.FileHandler(LOG_FILE,encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)

    mylog.addHandler(fh)
    mylog.addHandler(ch)
    return mylog
