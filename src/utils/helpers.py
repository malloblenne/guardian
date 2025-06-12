"""Helper functions and utilities."""

import logging
import sys


def setup_logging(level=logging.INFO):
    """Set up logging configuration."""
    logger = logging.getLogger(__name__)
    logger.setLevel(level)
    
    if not logger.handlers:
        log_hdlr = logging.StreamHandler(sys.stdout)
        log_hdlr.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        log_hdlr.setFormatter(formatter)
        logger.addHandler(log_hdlr)
    
    return logger
