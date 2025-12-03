from loguru import logger
import sys

logger.remove(0)
logger.add(sys.stdout, format="[{time}][{name}][{level}] - {message}: {process}")

