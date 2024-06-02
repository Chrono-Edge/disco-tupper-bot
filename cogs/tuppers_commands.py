from database.repositories.actor import ActorRepository
from database.repositories.user import UserRepository
from config import logger
from discord.ext import commands
import discord
import json
import typing
from builtins import str
from datetime import datetime
from typing import TYPE_CHECKING, Union

import config
import database.models.user
from database.models.actor import Actor
from database.models.user import User
from utils.encoding.non_printable import NonPrintableEncoder
from utils.encoding.non_printable import HEADER
from utils.tupper_template import parse_template

hidden_header = HEADER

if TYPE_CHECKING:
    from bot import DiscoTupperBot


class ListMenu(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.value = None

    @staticmethod
    async def actor_list_page(discord_user: discord.Member, page=0):
        user = await UserRepository.get_or_create_user(discord_user.id)
        embed = discord.Embed(colour=0x00b0f4,
                              timestamp=datetime.now())

        embed.set_author(name=f"{discord_user.display_name} actors")
        for actor in await user.actors.offset(page * 25).limit(25).all():
            embed.add_field(name=actor.name,
                            value=f"Actor call pattern: \n `{
                                actor.call_pattern}`",
                            inline=False)
        hidden_data = {"member_id": discord_user.id, "page": page}
        hidden_text = NonPrintableEncoder.encode(
            "Meta info", json.dumps(hidden_data).encode())
        embed.set_footer(text=hidden_text)
        return embed

    @discord.ui.button(label="Left", style=discord.ButtonStyle.blurple, custom_id='persistent_view:left')
    async def left_step(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = interaction.message.embeds[0]
        interaction.user.roles

        ___, hidden_data = NonPrintableEncoder.decode(embed.footer.text)
        meta_dict = json.loads(hidden_data)
        print()
        pass

    @discord.ui.button(label="Right", style=discord.ButtonStyle.blurple, custom_id='persistent_view:right')
    async def right_step(self, interaction: discord.Interaction, button: discord.ui.Button):

        embed = interaction.message.embeds[0]
        ___, hidden_data = NonPrintableEncoder.decode(embed.footer.text)
        meta_dict = json.loads(hidden_data)

        user = UserRepository.get_or_create_user(meta_dict["member_id"])

        print(hidden_data.decode())
        pass


class TupperCommandsCog(commands.Cog):
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot = bot
        self.reaction_to_edit = config.values.get("bot.reaction_to_edit")
        self.reaction_to_remove = config.values.get("bot.reaction_to_remove")
        self.admin_roles = config.values.get("bot.admin_roles")

    async def _user_is_admin(self, ctx: discord.ext.commands.Context):
        admin_roles = [discord.utils.get(
            ctx.guild.roles, name=role_name) for role_name in self.admin_roles]
        user_is_admin = False
        for admin_role in admin_roles:
            if admin_role in ctx.author.roles:
                user_is_admin = True
                break
        return user_is_admin

    async def _get_user_to_edit_actor(self, ctx: discord.ext.commands.Context, member: discord.Member) -> typing.Tuple[
            discord.Member, database.models.user.User]:

        if await self._user_is_admin(ctx) and member:
            member, user = await UserRepository.get_or_create_user(member.id)
            return member, user
        else:
            user = await UserRepository.get_or_create_user(ctx.author.id)
            return ctx.author, user

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
    async def create_actor(self, ctx: discord.ext.commands.Context, name: str, call_pattern: str,
                           avatar: discord.Attachment,
                           member: typing.Optional[discord.Member]):

        discord_user, user = await self._get_user_to_edit_actor(ctx, member)

        actor = None

        actor = await user.actors.filter(name=name).first()
        if actor:
            await ctx.reply("You already have actor with this name")
            return

        try:
            call_pattern = parse_template(call_pattern)
        except SyntaxError as e:
            await ctx.reply(str(e))

            return

        actor = await user.actors.filter(call_pattern=call_pattern)
        if actor:
            await ctx.reply("You already have actor with this call pattern")
            return

        actor = await ActorRepository.create_actor(name=name, call_pattern=call_pattern,
                                                   image=avatar.url)

        await user.actors.add(actor)

        await ctx.reply(f"Successful create actor: {actor.name}")
        webhook = await self._get_webhook(ctx.channel.id)
        await webhook.send("-- Hello World!", username=actor.name, avatar_url=actor.image)

    @commands.hybrid_command(name="remove_actor")
    @commands.has_any_role(*config.player_roles)
    async def remove_actor(self, ctx, name: str, member: typing.Optional[discord.Member]):
        discord_user, user = await self._get_user_to_edit_actor(ctx, member)

        actor = await user.actors.filter(name=name).first()

        if not actor:
            await ctx.reply(f"Cant find actor: {name}")
            return

        name = actor.name
        await ActorRepository.delete_actor(actor.id)
        await user.actors.add(actor)

        await ctx.reply(f"Successful remove actor: {name}")

    @commands.hybrid_command(name="edit_actor")
    @commands.has_any_role(*config.player_roles)
    async def edit_actor(self, ctx, actor_name: str, new_name: typing.Optional[str],
                         new_call_pattern: typing.Optional[str], member: typing.Optional[discord.Member]):
        parameter_list = ["name", "call_pattern", ]
        pass

    @commands.hybrid_command(name="set_inventory_chat_id")
    @commands.has_any_role(*config.player_roles)
    async def set_inventory_chat_id(self, ctx, name: str, member: typing.Optional[discord.Member]):
        pass

    @commands.hybrid_command(name="set_actor_avatar")
    @commands.has_any_role(*config.player_roles)
    async def set_actor_avatar(self, ctx, name: str, avatar: discord.Attachment,
                               member: typing.Optional[discord.Member]):
        print(ctx)
        print(name)
        print(avatar.url)
        await ctx.reply("Test")
        pass

    @commands.hybrid_command(name="add_user_to_actor")
    @commands.has_any_role(*config.player_roles)
    async def add_user_to_actor(self, ctx):
        pass

    @commands.hybrid_command(name="remove_user_to_actor")
    @commands.has_any_role(*config.player_roles)
    async def remove_user_from_actor(self, ctx):
        pass

    @commands.hybrid_command(name="actor_list")
    @commands.has_any_role(*config.player_roles)
    async def actor_list(self, ctx, member: typing.Optional[discord.Member]):
        view = ListMenu()
        discord_user, user = await self._get_user_to_edit_actor(ctx, member)
        embed = await ListMenu.actor_list_page(discord_user, 0)
        await ctx.reply(embed=embed, view=view)


async def setup(bot: "DiscoTupperBot"):
    await bot.add_cog(TupperCommandsCog(bot))
