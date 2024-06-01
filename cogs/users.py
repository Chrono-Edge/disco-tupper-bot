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
        local_user = await UserRepository.get_user_by_discord_id(member.id)
        if not local_user:
            await ctx.send(f"User already exist")
            return
        await UserRepository.create_user(member.id)
        await ctx.send(f"Create user {member.mention} in database")

    @commands.hybrid_command(name="remove_user")
    @commands.has_any_role(*config.admin_roles)
    async def remove_user(self, ctx: discord.ext.commands.Context, member: discord.Member):
        local_user = await UserRepository.get_user_by_discord_id(member.id)
        if not local_user:
            await local_user.delete()
            await ctx.send(f"User {member.mention} removed ")
            return
        await UserRepository.create_user(member.id)
        await ctx.send(f"User {member.mention} not exist in database")

    @commands.hybrid_command(name="sync_commands")
    @commands.has_any_role(*config.admin_roles)
    async def sync_commands(self, ctx: discord.ext.commands.Context):
        self.bot.tree.copy_global_to(guild=ctx.guild)
        if await self.bot.tree.sync():
            logger.success("Commands synced!")
            await ctx.send("Commands synced!")


async def setup(bot: "DiscoTupperBot"):
    await bot.add_cog(UserCog(bot))
