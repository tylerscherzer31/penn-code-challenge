import logging

# create logger using logging library
def create_logger():
    # create instance of logger
    logger = logging.getLogger()
    # capture log messages of info or higher
    logger.setLevel(logging.INFO)

    # check to see if the logger has an associated handler 
    if not logger.hasHandlers():
        # create a logger handler to output log messages to the console
        handler = logging.StreamHandler()
        # create and set log message formatter 
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        # attach the handler to the logger 
        logger.addHandler(handler)
    
    return logger