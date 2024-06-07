import discord

import config


class DiscordLogger:
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.log_channel = None
        pass

    async def send_log(self, content: str):
        if not self.log_channel:
            self.log_channel = await self.bot.fetch_channel(config.log_channel_id)

        await self.log_channel.send(f"```{content}```")
