import logging
import sys

from loguru import logger

from src.config import settings


class InterceptHandler(logging.Handler):
    """Redirige les logs du module logging standard vers loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
logger.remove()
logger.add(sys.stdout, level=settings.LOG_LEVEL)
