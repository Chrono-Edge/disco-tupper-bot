from typing import TYPE_CHECKING

import config
from utils.encoding.non_printable import NonPrintableEncoder

if TYPE_CHECKING:
    from bot import DiscoTupperBot

import discord
from discord.ext import commands
from config import logger
from database.repositories.user import UserRepository


class UserCog(commands.Cog):
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="create_user")
    @commands.has_any_role(*config.admin_roles)
    async def create_user(self, ctx: discord.ext.commands.Context, member: discord.Member):
        await UserRepository.create_user()
        await ctx.send(f"discord {member}")
        pass

    @commands.hybrid_command(name="remove_user")
    @commands.has_any_role(*config.admin_roles)
    async def remove_user(self, ctx: discord.ext.commands.Context, member: discord.Member):
        await ctx.send(f"discord {member}")
        pass


async def setup(bot: "DiscoTupperBot"):
    await bot.add_cog(UserCog(bot))
