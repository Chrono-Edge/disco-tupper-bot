from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot import DiscoTupperBot

import discord
from discord.ext import commands


class GreetingsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = member.guild.system_channel
        if channel is not None:
            await channel.send(f"Welcome {member.mention}.")

    @commands.hybrid_command(name="hello", aliases=["привет", "ку", "прувет"])
    async def hello(self, ctx, *, member: discord.Member = None):
        """Says hello"""
        member = member or ctx.author
        if self._last_member is None or self._last_member.id != member.id:
            await ctx.send(f"Hello {member.name}~")
        else:
            await ctx.send(f"Hello {member.name}... This feels familiar.")
        self._last_member = member


async def setup(bot: "DiscoTupperBot"):
    await bot.add_cog(GreetingsCog(bot))
