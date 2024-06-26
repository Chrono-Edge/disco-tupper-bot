﻿from discord.ext import commands

from utils.dices import roll_dices


class RollCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="roll", aliases=["r"])
    async def roll_dice(self, ctx, text: str):
        dice = await roll_dices(text)
        
        await ctx.send(f"{ctx.author.display_name}: {dice}")


async def setup(bot):
    await bot.add_cog(RollCog(bot))
