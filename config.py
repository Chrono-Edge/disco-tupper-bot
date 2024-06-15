import logging
import sys
from inspect import currentframe

from dynaconf import Dynaconf
from loguru import logger

values = Dynaconf(
    envvar_prefix="DYNACONF",
    settings_files=["settings.toml", ".secrets.toml"],
)

# `envvar_prefix` = export envvars with `export DYNACONF_FOO=bar`.
# `settings_files` = Load these files in the order.

token = values.get("secrets.token")
guild = values.get("secrets.guild")
sign_key = values.get("secrets.sign_key")

sign_key = sign_key.encode('UTF-8')
if len(sign_key) > 16:
    sign_key = sign_key[:16]
else:
    sign_key += b'a' * (16 - len(sign_key))

random_source = values.get("bot.random_source")

admin_roles = values.get("bot.admin_roles")
player_roles = values.get("bot.player_roles")

language = values.get("bot.language", "en")

prefixes = tuple(values.get("bot.prefixes", ()))

log_channel_id = values.get("bot.log_channel_id")

default_avatar_url = values.get("actor.default_avatar_url")

# Remove the existing logger
logger.remove()
# Add a new logger with the given settings
logger.add(
    sys.stdout,
    colorize=values.get("logging.colorize"),
    level=values.get("logging.level"),
    format=values.get("logging.format"),
)
# Add logging to file
logger.add(
    values.get("logging.file_path"),
    level=values.get("logging.level"),
    format=values.get("logging.format"),
    rotation=values.get("logging.rotation"),
    enqueue=values.get("logging.enqueue"),
)
logger.level("INFO", color="<blue>")

logger.info("Starting...")
logger.info("Configuration Initialization...")


class InterceptHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        super().__init__(level)

    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = currentframe(), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


icHandler = InterceptHandler()
# Create an interceptor for the loggers
logger_db_client = logging.getLogger("tortoise.db_client")
logger_db_client.setLevel(logging.DEBUG)
logger_db_client.addHandler(icHandler)

logger_tortoise = logging.getLogger("tortoise")
logger_tortoise.setLevel(logging.INFO)
logger_tortoise.addHandler(icHandler)

discord_log_handler = icHandler
logger.info("Configuration Initialized")
