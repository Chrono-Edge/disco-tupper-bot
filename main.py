from tortoise import run_async

from bot import bot
import config




def main():
    print("Starting bot...")
    run_async(bot.init_tortoise())
    
    #bot.run(token=config.token, log_handler=config.discord_log_handler, log_level="INFO")

if __name__ == "__main__":
    main()