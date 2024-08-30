import logging
import sys

def setup_logger(name: str, file_name: str = None) -> logging.Logger:
    """
    Logger configuration with both console and file handlers.

    The logger will output debug-level messages to the console and info-level
    messages to a file named 'app.log'. The log format includes the timestamp,
    logger name, log level, and message.

    Args:
        name (str): The name of the logger, typically the module's __name__.

    Returns:
        logging.Logger: A configured logger instance with handlers attached.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # File handler
    if file_name:
        file_handler = logging.FileHandler(file_name)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.addHandler(console_handler)


    return logger