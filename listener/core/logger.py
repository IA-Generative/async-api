import asyncio
import logging
import sys

from loguru import logger as loguru_logger


def get_task_name() -> str:
    """Récupère le nom de la tâche asyncio courante"""
    try:
        current_task = asyncio.current_task()
        return current_task.get_name() if current_task else "no-task"
    except RuntimeError:
        # Pas de boucle asyncio en cours
        return "no-task"


class InterceptHandler(logging.Handler):
    """Handler pour intercepter les logs du module logging standard et les rediriger vers loguru"""

    def emit(self, record) -> None:  # noqa: ANN001
        try:
            level = loguru_logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        loguru_logger.opt(depth=depth, exception=record.exc_info).log(
            level,
            record.getMessage(),
        )


def configure_logger(log_level: str = "INFO") -> None:
    """Configure loguru avec des couleurs et le format personnalisé"""
    log_level = log_level.upper()

    loguru_logger.remove()

    loguru_logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{extra[task_name]: <15}</cyan> | "
        "<yellow>{file.name}</yellow>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>",
        level=log_level,
        colorize=True,
        filter=lambda record: record["extra"].update(task_name=get_task_name()) or True,
    )

    logging.basicConfig(handlers=[InterceptHandler()], level=0)
    loggers_to_intercept = [
        "",
        "aio_pika",
        "asyncio",
    ]

    for logger_name in loggers_to_intercept:
        logging_logger = logging.getLogger(name=logger_name)
        logging_logger.handlers = [InterceptHandler()]
        logging_logger.setLevel(logging.INFO)
        logging_logger.propagate = False


logger = loguru_logger
