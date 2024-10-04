import hashlib
import math
import pathlib
import urllib.parse

from loguru import logger
from Crypto.Hash import SHA1
from database.models.user import User
from database.models.tupper import Tupper
from discord import app_commands
from discord.ext import commands
import discord
import typing
from builtins import str
from datetime import datetime
from typing import TYPE_CHECKING, Union
import config

import database.models.user
from utils.sign import Sign
from utils.content.image_upload import ImageStorage
from utils.encoding.non_printable import NonPrintableEncoder
from utils.discord.get_webhook import get_webhook
from utils.tupper_template import split_template
from utils.discord.permissions import Permissions
from localization import locale
from tupper_commands import Context

if TYPE_CHECKING:
    from bot import DiscoTupperBot


class TupperExtraCommandsCog(commands.Cog):
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot = bot
        self.admin_roles = config.values.get("bot.admin_roles")
        self.image_storage = ImageStorage()

    async def _get_webhook(
            self, channel_id: int
    ) -> tuple[discord.Webhook, discord.Thread]:
        return await get_webhook(self.bot, channel_id)

    @commands.command(aliases=['cft', 'кизт'])
    @app_commands.checks.has_any_role(*config.admin_roles)
    async def command_form_tapper(self, ctx: discord.ext.commands.Context, *, command: str):
        """Hidden edit for own tuppers and unhidden for another"""
        #TODO force move items and take and balance
        if not ctx.message.reference:
            await ctx.message.delete()
            # TODO relpy
            return

        channel = await self.bot.fetch_channel(ctx.message.reference.channel_id)
        ref_message = await channel.fetch_message(ctx.message.reference.message_id)
        _, dict_data = NonPrintableEncoder.decode_dict(ref_message.content)
        db_user_call_command = await User.filter(discord_id=ctx.author.id).first()
        #db_user_target_message = await User.filter(id=dict_data.get('author_id')).first()
        tupper = await Tupper.filter(id=dict_data.get("tupper_id")).first()

        if not tupper:
            await ctx.reply(locale.format("no_such_tupper", tupper_name=""))
            return

        command_output = await self.bot.tupper_commands.handle_command(
            tupper, ref_message, command
        )

        if not command_output:
            command_output = locale.format(
                "wrong_usage", command_name=command, usage=".help"
            )

        await self.bot.discord_logger.send_log(
            "log_do_command",
            log_author=ctx.message.author.name,
            log_tupper_name=tupper.name,
            log_command=command,
            log_result=command_output,
            log_jump_url=ctx.message.jump_url,
        )

        await ctx.message.delete()
        if db_user_call_command in await tupper.owners:
            command_output = f"`{tupper.name}`:\n{command_output}"
            await ctx.author.send(command_output + f"\n{ctx.message.reference.jump_url}")
        else:
            webhook, thread = await self._get_webhook(channel_id=ctx.channel.id)

            hidden_data = {"tupper_id": tupper.id, "author_id": ctx.author.id}
            files_content = []
            hidden_data["sign"] = Sign.sign(
                command_output, tupper.id, ctx.channel.id
            )
            message_content = NonPrintableEncoder.encode_dict(
                command_output, hidden_data
            )
            await webhook.send(
                message_content,
                username=tupper.name,
                avatar_url=tupper.image,
                files=files_content,
                thread=thread,
            )


async def setup(bot: "DiscoTupperBot"):
    await bot.add_cog(TupperExtraCommandsCog(bot))
