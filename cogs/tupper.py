from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot import DiscoTupperBot

import discord
from discord.ext import commands
from config import logger


class TupperCog(commands.Cog):
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.id == self.bot.user.id:
            return
        logger.info(message.content)
        await self.bot.process_commands(message)



async def setup(bot: "DiscoTupperBot"):
    await bot.add_cog(TupperCog(bot))
