from inspect import currentframe
import logging
import sys


from dynaconf import Dynaconf
from loguru import logger

settings = Dynaconf(
    envvar_prefix="DYNACONF",
    settings_files=['settings.toml', '.secrets.toml'],
)

# `envvar_prefix` = export envvars with `export DYNACONF_FOO=bar`.
# `settings_files` = Load these files in the order.

token = settings.get("bot.token")
debug_guild = settings.get("bot.debug_guild")


# Remove the existing logger
logger.remove()
# Add a new logger with the given settings
logger.add(
    sys.stdout,
    colorize=settings.get("logging.colorize"),
    level=settings.get("logging.level"),
    format=settings.get("logging.format"),
)
# Add logging to file
logger.add(
    settings.get("logging.file_path"),
    level=settings.get("logging.level"),
    format=settings.get("logging.format"),
    rotation=settings.get("logging.rotation"),
    enqueue=settings.get("logging.enqueue"),
)
logger.level("INFO", color="<blue>")

logger.info("Starting...")
logger.info("Configuration Initialization...")


class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = currentframe(), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

discord_log_handler = InterceptHandler()
logger.info("Configuration Initialized")
