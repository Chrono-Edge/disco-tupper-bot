import json
from builtins import str
from typing import TYPE_CHECKING, Union

import config
from database.models.actor import Actor
from database.models.user import User
from utils.encoding.non_printable import NonPrintableEncoder
from utils.encoding.non_printable import HEADER

hidden_header = HEADER

if TYPE_CHECKING:
    from bot import DiscoTupperBot

import discord
from discord.ext import commands
from config import logger
from database.repositories.user import UserRepository
from database.repositories.actor import ActorRepository


class TupperCog(commands.Cog):
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot = bot
        self.reaction_to_edit = config.values.get("bot.reaction_to_edit")
        self.reaction_to_remove = config.values.get("bot.reaction_to_remove")
        self.admin_roles = config.values.get("bot.admin_roles")

    async def _user_is_admin(self, ctx: discord.ext.commands.Context):
        admin_roles = [discord.utils.get(ctx.guild.roles, name=role_name) for role_name in self.admin_roles]
        user_is_admin = False
        for admin_role in admin_roles:
            if admin_role in ctx.author.roles:
                user_is_admin = True
                break
        return user_is_admin

    async def _get_webhook(self, channel_id: int):
        # TODO exception if limit of used webhooks
        channel = await self.bot.fetch_channel(channel_id)
        webhooks_list = await channel.webhooks()
        webhook = None
        for in_webhook in webhooks_list:
            if in_webhook.name == str(self.bot.user.id):
                webhook = in_webhook
        if not webhook:
            webhook = await channel.create_webhook(name=str(self.bot.user.id))
        return webhook

    @commands.command(name='test')
    async def test(self, ctx: discord.ext.commands.Context):
        await ctx.send("99 responce")

    @commands.command(name='get_info')
    async def get_mess_info(self, ctx, ch_id: int, mess_id: int):
        channel = await self.bot.fetch_channel(ch_id)
        message = await channel.fetch_message(mess_id)
        decode_text = NonPrintableEncoder.decode(message.content)
        logger.info(message.content)
        logger.info(decode_text.decode())
        await ctx.send(f"Hidden text {decode_text}")

    @commands.hybrid_command(name="create_actor")
    @commands.has_any_role(*config.player_roles)
    async def create_actor(self, ctx: discord.ext.commands.Context, name: str, call_pattern: str):
        user = await UserRepository.get_or_create_user(ctx.author.id)
        actor = await ActorRepository.create_actor(name=name, call_pattern=call_pattern,
                                                   image=config.values.get("actor.default_avatar_url"))
        await user.actors.add(actor)
        await ctx.reply(f"Successful create actor: {actor.name}")
        webhook = await self._get_webhook(ctx.channel.id)
        await webhook.send("-- Hello World!", username=actor.name, avatar_url=actor.image)

    @commands.hybrid_command(name="remove_actor")
    @commands.has_any_role(*config.player_roles)
    async def remove_actor(self, ctx, name: str):
        user = await UserRepository.get_or_create_user(ctx.author.id)
        actor = await user.actors.filter(name=name).first()
        if not actor:
            return
        name = actor.name
        await ActorRepository.delete_actor(actor.id)
        await user.actors.add(actor)

        await ctx.reply(f"Successful remove actor: {name}")

    @commands.hybrid_command(name="edit_actor")
    @commands.has_any_role(*config.player_roles)
    async def edit_actor(self, ctx, actor_name: str, parameter: str):
        parameter_list = ["name", "call_pattern", ]
        pass

    @commands.hybrid_command(name="set_inventory_chat_ud")
    @commands.has_any_role(*config.player_roles)
    async def set_inventory_chat_ud(self, ctx, name: str):
        pass

    @commands.hybrid_command(name="set_actor_avatar")
    @commands.has_any_role(*config.player_roles)
    async def set_actor_avatar(self, ctx, member: discord.Member):
        pass

    @commands.hybrid_command(name="add_user_to_actor")
    @commands.has_any_role(*config.player_roles)
    async def add_user_to_actor(self, ctx):
        pass

    @commands.hybrid_command(name="remove_user_to_actor")
    @commands.has_any_role(*config.player_roles)
    async def remove_user_from_actor(self, ctx):
        pass


async def setup(bot: "DiscoTupperBot"):
    await bot.add_cog(TupperCog(bot))
