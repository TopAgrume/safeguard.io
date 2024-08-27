import functools
from logzero import logger

def debug_logger(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        logger.debug(f"API: {func.__name__} call")
        return await func(*args, **kwargs)
    return wrapper
