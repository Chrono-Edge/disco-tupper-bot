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

    @commands.command(aliases=['cft'])
    @app_commands.checks.has_any_role(*config.admin_roles)
    async def command_form_tapper(self, ctx: discord.ext.commands.Context):
        """Hidden edit for own tuppers and unhidden for another"""
        print(ctx.message.type)
        channel = await self.bot.fetch_channel(ctx.message.reference.channel_id)
        message = await channel.fetch_message(ctx.message.reference.message_id)
        message, dict_data = NonPrintableEncoder.decode_dict(message.content)
        tupper = await Tupper.filter(id=dict_data.get(''))

        print(dict_data)

        # NonPrintableEncoder.decode_dict()


async def setup(bot: "DiscoTupperBot"):
    await bot.add_cog(TupperExtraCommandsCog(bot))
