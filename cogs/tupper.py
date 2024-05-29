from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot import DiscoTupperBot

import discord
from discord.ext import commands


class TupperCog(commands.Cog):
    def __init__(self, bot: "DiscoTupperBot"):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        print(message)



async def setup(bot: "DiscoTupperBot"):
    await bot.add_cog(TupperCog(bot))
