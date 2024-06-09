import math

from database.models.user import User
from database.models.tupper import Tupper
from config import logger
from discord.ext import commands
import discord
import typing
from builtins import str
from datetime import datetime
from typing import TYPE_CHECKING, Union
import config

import database.models.user
from utils.discord.action_logger import DiscordLogger
from utils.encoding.non_printable import NonPrintableEncoder
from utils.discord.get_webhook import get_webhook
from utils.tupper_template import parse_template
from utils.discord.permissions import Permissions
from localization import locale
from utils.tupper_template import unparse_template
from tupper_commands import Context

if TYPE_CHECKING:
    from bot import DiscoTupperBot


class ListMenu(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.value = None

    @staticmethod
    async def tupper_list_page(
        client: discord.Client,
        discord_user: Union[discord.User, discord.Member],
        page=0,
    ):
        user, _ = await User.get_or_create(discord_id=discord_user.id)

        embeds_list = []

        hidden_data = {"member_id": discord_user.id, "page": page}
        hidden_text = NonPrintableEncoder.encode_dict("", hidden_data)

        for tupper in await user.tuppers.offset(page * 10).limit(10).all():
            embed = discord.Embed(colour=0x00B0F4, timestamp=datetime.now())
            embed.set_author(name=f"{tupper.name}")

            human_like_call_pattern = unparse_template(tupper.call_pattern)
            human_like_owners = [
                await client.fetch_user(user.discord_id)
                for user in await tupper.owners.all()
            ]
            human_like_owners = [f"`{user.name}`" for user in human_like_owners]
            human_like_owners = " ".join(human_like_owners)

            embed.add_field(
                name=locale.tupper_info,
                value=locale.format(
                    "tupper_info_desc",
                    call_pattern=human_like_call_pattern,
                    owners=human_like_owners,
                ),
                inline=False,
            )
            embed.set_thumbnail(url=tupper.image)
            embeds_list.append(embed)

        return hidden_text, embeds_list

    @discord.ui.button(
        label="Left",
        style=discord.ButtonStyle.blurple,
        custom_id="persistent_view:left",
    )
    async def left_step(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        client = interaction.client
        _, meta_dict = NonPrintableEncoder.decode_dict(interaction.message.content)

        if ("member_id" not in meta_dict) and ("page" not in meta_dict):
            return

        member_id = meta_dict.get("member_id")
        page = meta_dict.get("page")

        page = page - 1
        if page < 0:
            page = 0

        member = await interaction.guild.fetch_member(member_id)
        is_user_admin = await Permissions.is_user_admin(
            config.admin_roles, member, interaction.guild
        )

        if (interaction.user.id != member_id) and not is_user_admin:
            return

        message, embeds = await ListMenu.tupper_list_page(client, member, page)
        await interaction.response.edit_message(content=message, embeds=embeds)

    @discord.ui.button(
        label="Right",
        style=discord.ButtonStyle.blurple,
        custom_id="persistent_view:right",
    )
    async def right_step(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        client = interaction.client
        _, meta_dict = NonPrintableEncoder.decode_dict(interaction.message.content)

        if ("member_id" not in meta_dict) and ("page" not in meta_dict):
            return

        member_id = meta_dict.get("member_id")
        page = meta_dict.get("page")
        if interaction.user.id != member_id:
            return

        user, ___ = await User.get_or_create(discord_id=member_id)

        page = page + 1
        max_page = math.ceil(await user.tuppers.all().count() / 10) - 1
        if page > max_page:
            page = max_page

        member = await interaction.guild.fetch_member(member_id)
        is_user_admin = await Permissions.is_user_admin(
            config.admin_roles, member, interaction.guild
        )

        if (interaction.user.id != member_id) and not is_user_admin:
            return

        message, embeds = await ListMenu.tupper_list_page(client, member, page)
        await interaction.response.edit_message(content=message, embeds=embeds)


class TupperCommandsCog(commands.Cog):
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot = bot
        self.discord_logger = DiscordLogger(self.bot)
        self.reaction_to_edit = config.values.get("bot.reaction_to_edit")
        self.reaction_to_remove = config.values.get("bot.reaction_to_remove")
        self.admin_roles = config.values.get("bot.admin_roles")

    async def _get_user_to_edit_tupper(
        self, ctx: discord.ext.commands.Context, member: discord.Member
    ) -> typing.Tuple[discord.Member, database.models.user.User]:
        """get current user as target or specified by admin"""
        if await Permissions.get_user_is_admin(self.admin_roles, ctx) and member:
            user, _ = await User.get_or_create(discord_id=member.id)
            return member, user
        user, _ = await User.get_or_create(discord_id=ctx.author.id)
        return ctx.author, user

    async def _get_webhook(
        self, channel_id: int
    ) -> tuple[discord.Webhook, discord.Thread]:
        return await get_webhook(self.bot, channel_id)

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
        """Create new tupper."""
        _, user = await self._get_user_to_edit_tupper(ctx, member)

        if await user.tuppers.filter(name=name).first():
            await ctx.reply(locale.tupper_already_exists)

            return

        orig_call_pattern = call_pattern

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

        await ctx.reply(
            locale.format(
                "tupper_was_successfully_created",
                tupper_name=tupper.name,
            )
        )

        await self.discord_logger.send_log(
            "log_create_tupper",
            log_author=ctx.message.author.name,
            log_tupper_name=tupper.name,
            log_tupper_call_pattern=orig_call_pattern,
            log_jump_url=ctx.message.jump_url,
        )

    @commands.hybrid_command(name="remove_tupper")
    @commands.has_any_role(*config.player_roles)
    async def remove_tupper(
        self,
        ctx: discord.ext.commands.Context,
        tupper_name: str,
        member: typing.Optional[discord.Member],
    ):
        """Delete existing tupper."""
        _, user = await self._get_user_to_edit_tupper(ctx, member)

        tupper = await user.tuppers.filter(name=tupper_name).first()

        if not tupper:
            await ctx.reply(locale.format("no_such_tupper", tupper_name=tupper_name))
            return

        tupper_name = tupper.name
        await Tupper.filter(id=tupper.id).delete()

        await ctx.reply(locale.tupper_was_successfully_removed)

        await self.discord_logger.send_log(
            "log_remove_tupper",
            log_author=ctx.message.author.name,
            log_tupper_name=tupper_name,
            log_jump_url=ctx.message.jump_url,
        )

    @commands.hybrid_command(name="edit_tupper")
    @commands.has_any_role(*config.player_roles)
    async def edit_tupper(
        self,
        ctx: discord.ext.commands.Context,
        tupper_name: str,
        new_name: typing.Optional[str],
        new_call_pattern: typing.Optional[str],
        avatar: typing.Optional[discord.Attachment],
        tupper_owner: typing.Optional[discord.Member],
    ):
        """Edit tupper."""
        _, user = await self._get_user_to_edit_tupper(ctx, tupper_owner)

        tupper: Tupper = await user.tuppers.filter(name=tupper_name).first()

        log_keys = {}

        if not tupper:
            await ctx.reply(locale.no_such_tupper)
            return

        if new_name:
            tupper_with_name = await user.tuppers.filter(
                call_pattern=new_call_pattern
            ).first()
            if tupper_with_name:
                await ctx.reply(locale.tupper_already_exists)
                return
            tupper.name = new_name
            log_keys["log_tupper_name"] = new_name

        if new_call_pattern:
            try:
                new_call_pattern = parse_template(new_call_pattern)
            except SyntaxError as e:
                await ctx.reply(str(e))
                return

            tupper_with_pattern = await user.tuppers.filter(
                call_pattern=new_call_pattern
            ).first()
            if tupper_with_pattern:
                await ctx.reply(locale.tupper_already_exists)
                return
            tupper.call_pattern = new_call_pattern
            log_keys["log_tupper_call_pattern"] = new_call_pattern

        if avatar:
            tupper.image = avatar.url

        await tupper.save()
        await ctx.reply(
            locale.format("successful_edit_tupper", tupper_name=tupper_name)
        )

        await self.discord_logger.send_log(
            "log_edit_tupper",
            log_author=ctx.message.author.name,
            **log_keys,
            log_jump_url=ctx.message.jump_url,
        )

    @commands.hybrid_command(name="set_inventory_chat")
    @commands.has_any_role(*config.player_roles)
    async def set_inventory_chat_id(
        self,
        ctx: discord.ext.commands.Context,
        member: typing.Optional[discord.Member],
        tupper_name: str,
    ):
        """Set inventory chat for a tupper."""
        _, user = await self._get_user_to_edit_tupper(ctx, member)

        tupper: Tupper = await user.tuppers.filter(name=tupper_name).first()
        if not tupper:
            await ctx.reply(locale.no_such_tupper)
            return

        tupper.inventory_chat_id = ctx.channel.id
        await tupper.save()

        await ctx.reply(locale.format("set_inventory_chat", tupper_name=tupper_name))

        await self.discord_logger.send_log(
            "log_set_inventory_chat",
            log_author=ctx.message.author.name,
            log_tupper_name=tupper.name,
            log_inventory_chat_id=tupper.inventory_chat_id,
            log_jump_url=ctx.message.jump_url,
        )

    @commands.hybrid_command(name="add_user_to_tupper")
    @commands.has_any_role(*config.player_roles)
    async def add_user_to_tupper(
        self,
        ctx: discord.ext.commands.Context,
        tupper_name: str,
        user_add: discord.Member,
        tupper_owner: typing.Optional[discord.Member],
    ):
        """Add user to a tupper."""
        _, target_user = await self._get_user_to_edit_tupper(ctx, tupper_owner)
        user_to_add, _ = await User.get_or_create(discord_id=user_add.id)
        tupper: Tupper = await target_user.tuppers.filter(name=tupper_name).first()

        if not tupper:
            await ctx.reply(locale.no_such_tupper)
            return

        await user_to_add.tuppers.add(tupper)
        await ctx.reply(
            locale.format(
                "add_owner_form_tupper",
                tupper_name=tupper_name,
                user_mention=user_add.mention,
            )
        )

        await self.discord_logger.send_log(
            "log_tupper_add_user",
            log_author=ctx.message.author.name,
            log_tupper_name=tupper.name,
            log_user=user_add.name,
            log_jump_url=ctx.message.jump_url,
        )

    @commands.hybrid_command(name="remove_user_from_tupper")
    @commands.has_any_role(*config.player_roles)
    async def remove_user_from_tupper(
        self,
        ctx: discord.ext.commands.Context,
        tupper_name: str,
        user_remove: discord.Member,
        tupper_owner: typing.Optional[discord.Member],
    ):
        """Remove user from a tupper."""
        _, target_user = await self._get_user_to_edit_tupper(ctx, tupper_owner)
        user_to_add = await User.get(discord_id=user_remove.id)

        tupper: Tupper = await target_user.tuppers.filter(name=tupper_name).first()
        if not tupper:
            await ctx.reply(locale.no_such_tupper)
            return

        await user_to_add.tuppers.remove(tupper)

        if tupper.owners.all().count() == 0:
            await tupper.delete()
            await ctx.reply(
                locale.format("tupper_not_used_and_remove", tupper_name=tupper_name)
            )

        await ctx.reply(
            locale.format(
                "remove_owner_from_tupper",
                tupper_name=tupper_name,
                user_mention=user_remove.mention,
            )
        )

        await self.discord_logger.send_log(
            "log_tupper_remove_user",
            log_author=ctx.message.author.name,
            log_tupper_name=tupper.name,
            log_user=user_remove.name,
            log_jump_url=ctx.message.jump_url,
        )

    @commands.hybrid_command(name="tupper_list")
    @commands.has_any_role(*config.player_roles)
    async def tupper_list(self, ctx, member: typing.Optional[discord.Member]):
        """List all tuppers for a user."""
        view = None
        discord_user, _ = await self._get_user_to_edit_tupper(ctx, member)
        message, embeds = await ListMenu.tupper_list_page(self.bot, discord_user, 0)
        user = await User.filter(discord_id=discord_user.id).first()

        count_tuppers = await user.tuppers.all().count()
        if count_tuppers == 0:
            await ctx.reply(locale.empty)

            return

        if count_tuppers > 10:
            view = ListMenu()

        await ctx.reply(content=message, embeds=embeds, view=view)

    @commands.hybrid_command(name="admin_balance_set")
    @commands.has_any_role(*config.admin_roles)
    async def admin_balance_set(
        self,
        ctx: discord.ext.commands.Context,
        tupper_owner: typing.Optional[discord.Member],
        tupper_name: str,
        balance: int,
    ):
        """Add balance for a tupper."""
        _, target_user = await self._get_user_to_edit_tupper(ctx, tupper_owner)

        tupper: Tupper = await target_user.tuppers.filter(name=tupper_name).first()
        if not tupper:
            await ctx.reply(locale.no_such_tupper)
            return

        old_balance = tupper.balance
        tupper.balance = tupper.balance + balance
        await tupper.save()
        await ctx.reply(
            locale.format("admin_balance_add", tupper_name=tupper_name, balance=balance)
        )

        await self.discord_logger.send_log(
            "log_add_balance",
            log_author=ctx.message.author.name,
            log_tupper_name=tupper.name,
            log_quantity=balance,
            log_jump_url=ctx.message.jump_url,
        )

        # >:)
        pseudo_ctx = Context(
            bot=self.bot, tupper=tupper, message=ctx.message, command=None
        )
        await pseudo_ctx.log(
            "log_incoming_balance",
            log_quantity=balance,
            log_author=ctx.message.author.name,
            log_old_balance=old_balance,
            log_new_balance=tupper.balance,
            log_jump_url=ctx.message.jump_url,
        )


async def setup(bot: "DiscoTupperBot"):
    await bot.add_cog(TupperCommandsCog(bot))
