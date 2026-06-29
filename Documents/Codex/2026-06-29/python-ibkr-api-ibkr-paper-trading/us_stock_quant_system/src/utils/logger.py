from loguru import logger

from .config_loader import load_all_configs
from .paths import LOGS_DIR


def setup_logger() -> None:
    configs = load_all_configs()
    level = configs["settings"].get("logging", {}).get("level", "INFO")
    logger.remove()
    logger.add(LOGS_DIR / "system.log", rotation="2 MB", retention=5, level=level)
    logger.add(lambda msg: print(msg, end=""), level=level)
