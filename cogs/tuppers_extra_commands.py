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

    @commands.command(aliases=['aea'])
    @app_commands.checks.has_any_role(*config.admin_roles)
    async def admin_edit_attribute(self, ctx):
        """Hidden edit for own tuppers and unhidden for another"""
        pass


async def setup(bot: "DiscoTupperBot"):
    await bot.add_cog(TupperExtraCommandsCog(bot))
