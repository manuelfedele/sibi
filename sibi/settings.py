import sys

from loguru import logger

fmt = '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: ^8}</level> | ' \
      '<cyan>{name: <20}</cyan> | <cyan>{function: <20}</cyan> | ' \
      '<cyan>{line: ^4}</cyan> | <level>{message}</level>'

logger.configure(
    handlers=[
        {"sink": sys.stdout, "format": fmt, "level": "INFO"},
    ],
)
