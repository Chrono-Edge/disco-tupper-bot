import asyncio
from typing import TYPE_CHECKING

import config
from utils.encoding.non_printable import NonPrintableEncoder

if TYPE_CHECKING:
    from bot import DiscoTupperBot

import discord
from discord.ext import commands
from config import logger
from database.models.user import User
from localization import locale

class UserCog(commands.Cog):
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="admin_create_user")
    @commands.has_any_role(*config.admin_roles)
    async def create_user(self, ctx: discord.ext.commands.Context, member: discord.Member):
        local_user = await User.get(discord_id=member.id)
        if not local_user:
            await ctx.send(locale.user_already_exists)
            return
        await User.create(discord_id=member.id)
        await ctx.send(locale.user_was_successfully_created)

    @commands.hybrid_command(name="admin_remove_user")
    @commands.has_any_role(*config.admin_roles)
    async def remove_user(self, ctx: discord.ext.commands.Context, member: discord.Member):
        local_user = await User.get(discord_id=member.id)
        if not local_user:
            await local_user.delete()
            await ctx.send(locale.user_was_successfully_removed)
            return

        await ctx.send(locale.user_does_not_exist)

    @commands.hybrid_command(name="sync_commands")
    @commands.has_any_role(*config.admin_roles)
    async def sync_commands(self, ctx: discord.ext.commands.Context):
        """Sync all commands"""
        self.bot.tree.copy_global_to(guild=ctx.guild)
        if await self.bot.tree.sync():
            await asyncio.sleep(2)
            logger.success("Commands synced!")
            await ctx.send("Commands synced!")


async def setup(bot: "DiscoTupperBot"):
    await bot.add_cog(UserCog(bot))
