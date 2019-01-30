import logging


def create_logger(logfile):
    """
    Creates a logging object and returns it
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # set pdfminer logger to error mode

    # logging.propagate = False

    # create the logging file handler
    fh = logging.FileHandler(logfile)
    fh.setLevel(logging.INFO)
    fmt = '%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)d - %(message)s'
    formatter = logging.Formatter(fmt)
    fh.setFormatter(formatter)

    # add handler to logger object
    logger.addHandler(fh)

    logging.getLogger("pdfminer").setLevel(logging.ERROR)
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
