import re
from database.models.user import User
from database.models.tupper import Tupper
from config import logger
from discord.ext import commands
import discord
import json
import typing
from builtins import str
from datetime import datetime
from typing import TYPE_CHECKING

import config
import database.models.user
from database.models.attribute import Attribute
from utils.encoding.non_printable import NonPrintableEncoder, HEADER
from utils.tupper_command import get_webhook
from utils.tupper_template import parse_template
from utils.discord.permissions import Permissions
from localization import locale

hidden_header = HEADER

if TYPE_CHECKING:
    from bot import DiscoTupperBot


class ListMenu(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.value = None

    @staticmethod
    async def tupper_list_page(discord_user: discord.Member, page=0):
        user = await User.get_or_create(discord_id=discord_user.id)
        embed = discord.Embed(colour=0x00B0F4, timestamp=datetime.now())

        embed.set_author(name=f"Тапперы {discord_user.display_name}:")
        for tupper in await user.tuppers.offset(page * 25).limit(25).all():
            embed.add_field(
                name=tupper.name,
                value=locale.format(
                    "tupper_call_pattern", call_pattern=tupper.call_pattern
                ),
                inline=False,
            )
        hidden_data = {"member_id": discord_user.id, "page": page}
        hidden_text = NonPrintableEncoder.encode(
            "Meta info", json.dumps(hidden_data).encode()
        )
        embed.set_footer(text=hidden_text)
        return embed

    @discord.ui.button(
        label="Left",
        style=discord.ButtonStyle.blurple,
        custom_id="persistent_view:left",
    )
    async def left_step(
            self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = interaction.message.embeds[0]
        interaction.user.roles

        _, hidden_data = NonPrintableEncoder.decode(embed.footer.text)
        meta_dict = json.loads(hidden_data)
        print()
        pass

    @discord.ui.button(
        label="Right",
        style=discord.ButtonStyle.blurple,
        custom_id="persistent_view:right",
    )
    async def right_step(
            self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = interaction.message.embeds[0]
        _, hidden_data = NonPrintableEncoder.decode(embed.footer.text)
        meta_dict = json.loads(hidden_data)

        user = await User.get_or_create(discord_id=meta_dict["member_id"])

        print(hidden_data.decode())
        pass


class TupperCommandsCog(commands.Cog):
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot = bot
        self.reaction_to_edit = config.values.get("bot.reaction_to_edit")
        self.reaction_to_remove = config.values.get("bot.reaction_to_remove")
        self.admin_roles = config.values.get("bot.admin_roles")

    async def _get_user_to_edit_tupper(
            self, ctx: discord.ext.commands.Context, member: discord.Member
    ) -> typing.Tuple[discord.Member, database.models.user.User]:
        """get current user as target or specified  by admin"""
        if await Permissions.get_user_is_admin(self.admin_roles, ctx) and member:
            user, ___ = await User.get_or_create(discord_id=member.id)
            return member, user
        user, ___ = await User.get_or_create(discord_id=ctx.author.id)
        return ctx.author, user

    async def _get_webhook(self, channel_id: int):
        return get_webhook(self.bot, channel_id)

    @commands.hybrid_command(name="create_tupper")
    @commands.has_any_role(*config.player_roles)
    async def create_tupper(
            self,
            ctx: discord.ext.commands.Context,
            name: str,
            call_pattern: str,
            avatar: discord.Attachment,
            member: typing.Optional[discord.Member],
    ):
        """Create new tupper"""
        _, user = await self._get_user_to_edit_tupper(ctx, member)

        if await user.tuppers.filter(name=name).first():
            await ctx.reply(locale.tupper_already_exists)

            return

        try:
            call_pattern = parse_template(call_pattern)
        except SyntaxError as e:
            await ctx.reply(str(e))

            return

        if await user.tuppers.filter(call_pattern=call_pattern).first():
            await ctx.reply(locale.tupper_already_exists)

            return

        tupper = await Tupper.create(
            name=name, call_pattern=call_pattern, image=avatar.url
        )
        await user.tuppers.add(tupper)

        await ctx.reply(locale.tupper_was_successfully_created)

    @commands.hybrid_command(name="remove_tupper")
    @commands.has_any_role(*config.player_roles)
    async def remove_tupper(
            self, ctx, name: str, member: typing.Optional[discord.Member]
    ):
        _, user = await self._get_user_to_edit_tupper(ctx, member)

        tupper = await user.tuppers.filter(name=name).first()

        if not tupper:
            await ctx.reply(locale.format("no_such_tupper", tupper_name=name))
            return

        name = tupper.name
        await Tupper.filter(id=tupper.id).delete()

        await ctx.reply(locale.tupper_was_successfully_removed)

    @commands.hybrid_command(name="edit_tupper")
    @commands.has_any_role(*config.player_roles)
    async def edit_tupper(
            self,
            ctx: discord.ext.commands.Context,
            tupper_name: str,
            new_name: typing.Optional[str],
            new_call_pattern: typing.Optional[str],
            avatar: typing.Optional[discord.Attachment],
            member: typing.Optional[discord.Member],
    ):
        _, user = await self._get_user_to_edit_tupper(ctx, member)

        tupper: Tupper = await user.tuppers.filter(name=tupper_name).first()

        if not tupper:
            await ctx.reply(locale.no_such_tupper)
            return

        if new_name:
            tupper.name = new_name

        if new_call_pattern:
            try:
                new_call_pattern = parse_template(new_call_pattern)
            except SyntaxError as e:
                await ctx.reply(str(e))
                return
            tupper.call_pattern = new_call_pattern

        if avatar:
            tupper.image = avatar.url

        if member:
            if await user.tuppers.filter(
                    name=new_name if new_name else tupper.name
            ).first():
                await ctx.reply(locale.tupper_already_exists)
                return

            if await user.tuppers.filter(
                    call_pattern=new_call_pattern
                    if new_call_pattern
                    else tupper.call_pattern
            ).first():
                await ctx.reply(locale.tupper_already_exists)
                return

            await user.tuppers.add(tupper)

        await tupper.save()

    @commands.hybrid_command(name="set_inventory_chat")
    @commands.has_any_role(*config.player_roles)
    async def set_inventory_chat_id(
            self, ctx: discord.ext.commands.Context,
            member: typing.Optional[discord.Member], tupper_name: str
    ):
        _, user = await self._get_user_to_edit_tupper(ctx, member)

        tupper: Tupper = await user.tuppers.filter(name=tupper_name).first()

        tupper.inventory_chat_id = ctx.channel.id
        await tupper.save()

        await ctx.reply("Inventory set chat")

    @commands.hybrid_command(name="add_user_to_tupper")
    @commands.has_any_role(*config.player_roles)
    async def add_user_to_tupper(self, ctx: discord.ext.commands.Context,
                                 tupper_name: str,
                                 user_add: discord.Member,
                                 tupper_owner: typing.Optional[discord.Member]):
        _, target_user = await self._get_user_to_edit_tupper(ctx, tupper_owner)
        user_to_add = await User.get(discord_id=user_add.id)

        tupper: Tupper = await target_user.tuppers.filter(name=tupper_name).first()
        await user_to_add.tuppers.add(tupper)
        await ctx.reply("Add tupper {name} ({owner}) to user {user_add}")

    @commands.hybrid_command(name="remove_user_to_tupper")
    @commands.has_any_role(*config.player_roles)
    async def remove_user_from_tupper(self, ctx: discord.ext.commands.Context,
                                      tupper_name: str,
                                      user_add: discord.Member,
                                      tupper_owner: typing.Optional[discord.Member]):
        _, target_user = await self._get_user_to_edit_tupper(ctx, tupper_owner)
        user_to_add = await User.get(discord_id=user_add.id)

        tupper: Tupper = await target_user.tuppers.filter(name=tupper_name).first()
        await user_to_add.tuppers.remove(tupper)

        await ctx.reply("Add tupper {name} ({owner}) to user {user_add}")

    @commands.hybrid_command(name="tupper_list")
    @commands.has_any_role(*config.player_roles)
    async def tupper_list(self, ctx, member: typing.Optional[discord.Member]):
        view = ListMenu()
        discord_user, _ = await self._get_user_to_edit_tupper(ctx, member)
        embed = await ListMenu.tupper_list_page(discord_user, 0)

        await ctx.reply(embed=embed, view=view)

    @commands.hybrid_command(name="set_attribute")
    @commands.has_any_role(*config.player_roles)
    async def set_attr(
            self,
            ctx: discord.ext.commands.Context,
            member: typing.Optional[discord.Member],
            tupper_name: str,
            name: str,
            value: int,
    ):
        name = name.lower()
        if not re.match(r"^[а-яa-z]{2,3}$", name):
            await ctx.reply(locale.illegal_attribute_name)
            return

        _, user = await self._get_user_to_edit_tupper(ctx, member)
        tupper = await user.tuppers.filter(name=tupper_name).first()

        if not tupper:
            await ctx.reply(locale.no_such_tupper)
            return

        attr = await tupper.attrs.filter(name=name).first()

        if not attr:
            await Attribute.create(owner=tupper, name=name, value=value)
            return

        await attr.update(value=value)
        await ctx.reply(locale.attribute_was_successfully_changed)

    @commands.hybrid_command(name="balance")
    @commands.has_any_role(*config.player_roles)
    async def balance(
            self, ctx, member: typing.Optional[discord.Member], tupper_name: str
    ):
        _, user = await self._get_user_to_edit_tupper(ctx, member)

        tupper = await user.tuppers.filter(name=tupper_name).first()

        if not tupper:
            await ctx.reply(locale.no_such_tupper)
            return

        await ctx.reply(locale.format("current_balance", tupper.balance))

    @commands.hybrid_command(name="add_balance")
    @commands.has_any_role(*config.admin_roles)
    async def admin_add_balance(
            self,
            ctx,
            member: discord.Member,
            tupper_name: str,
            amount: int,
    ):
        _, user = await self._get_user_to_edit_tupper(ctx, member)

        tupper = await user.tuppers.filter(name=tupper_name).first()

        if not tupper:
            await ctx.reply(locale.no_such_tupper)
            return

        balance = abs(tupper.balance + amount)
        await tupper.update(balance=balance)
        await tupper.save()

        await ctx.reply(locale.format("current_balance", balance))

    @commands.hybrid_command(name="send_balance")
    @commands.has_any_role(*config.player_roles)
    async def send_balance(
            self,
            ctx,
            from_member: typing.Optional[discord.Member],
            from_tupper_name: str,
            to_member: discord.Member,
            to_tupper_name: str,
            amount: int,
    ):
        _, from_user = await self._get_user_to_edit_tupper(ctx, from_member)

        from_tupper = await from_user.tuppers.filter(name=from_tupper_name).first()

        to_user = await User.get(discord_id=to_member.id)

        to_tupper = await to_user.tuppers.filter(name=to_tupper_name).first()

        if not from_tupper:
            await ctx.reply(locale.no_such_tupper)
            return

        if not to_tupper:
            await ctx.reply(locale.no_such_tupper)
            return

        if amount > from_tupper.balance:
            await ctx.reply(
                locale.format(
                    "balance_is_too_low", need=amount, have=from_tupper.balance
                )
            )
            return

        new_balance = from_tupper.balance - amount
        await from_tupper.update(balance=new_balance)
        await to_tupper.update(balance=to_tupper.balance + amount)

        await ctx.reply(locale.format("current_balance", balance=new_balance))


async def setup(bot: "DiscoTupperBot"):
    await bot.add_cog(TupperCommandsCog(bot))
