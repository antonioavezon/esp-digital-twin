import logging
import os


def configure_logging() -> logging.Logger:
    logger = logging.getLogger("esp.core")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("ESP-CORE | %(message)s"))
        logger.addHandler(handler)
        logger.propagate = False
    logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))
    return logger
