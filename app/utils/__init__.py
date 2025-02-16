import os
import sys
import time
from pathlib import Path

from loguru import logger  # type: ignore

os.environ["TZ"] = "Europe/Kyiv"
time.tzset()
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add(
    LOGS_DIR / "app.log",
    rotation="10 MB",
    retention="7 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}",
)
