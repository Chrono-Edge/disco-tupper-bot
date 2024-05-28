from bot import bot
import config

bot.run(token=config.token, log_handler=config.discord_log_handler, log_level="INFO")
