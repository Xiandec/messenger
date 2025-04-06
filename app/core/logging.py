import logging
from typing import Any

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger("messenger")

def log_info(message: str, *args: Any, **kwargs: Any) -> None:
    logger.info(message, *args, **kwargs)

def log_error(message: str, *args: Any, **kwargs: Any) -> None:
    logger.error(message, *args, **kwargs)

def log_warning(message: str, *args: Any, **kwargs: Any) -> None:
    logger.warning(message, *args, **kwargs)

def log_debug(message: str, *args: Any, **kwargs: Any) -> None:
    logger.debug(message, *args, **kwargs) 