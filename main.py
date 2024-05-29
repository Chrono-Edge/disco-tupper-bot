from tortoise import run_async

import config
from bot import bot


def main():
    config.logger.info("Starting bot...")
    run_async(bot.init_tortoise())

    bot.run(token=config.token, log_handler=config.discord_log_handler, log_level="INFO")


if __name__ == "__main__":
    main()
