from config import logger
from discord.ext import commands
import discord
import re
import json
from builtins import str
from typing import TYPE_CHECKING

import config
from database.models.user import User
from utils.encoding.non_printable import NonPrintableEncoder
from utils.encoding.non_printable import HEADER
from utils.tupper_command import handle_tupper_command, get_webhook
from localization import locale

hidden_header = HEADER

if TYPE_CHECKING:
    from bot import DiscoTupperBot


class TupperMessageCog(commands.Cog):
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot = bot
        self.reaction_to_edit = config.values.get("bot.reaction_to_edit")
        self.reaction_to_remove = config.values.get("bot.reaction_to_remove")

    async def _get_webhook(self, channel_id: int):
        return await get_webhook(self.bot, channel_id)

    async def _remove_message(
            self, payload: discord.RawReactionActionEvent, db_user: User, metadata_dict
    ):
        if str(payload.emoji) != self.reaction_to_remove:
            return
        tupper = await db_user.tuppers.filter(id=metadata_dict["tupper_id"]).first()
        if not tupper:
            return
        webhook = await self._get_webhook(payload.channel_id)
        await webhook.delete_message(payload.message_id)

    async def _create_edit_message(
            self, payload: discord.RawReactionActionEvent, db_user: User, metadata_dict
    ):
        if str(payload.emoji) != self.reaction_to_edit:
            return
        tupper = await db_user.tuppers.filter(id=metadata_dict["tupper_id"]).first()
        if not tupper:
            return

        user = await self.bot.fetch_user(payload.user_id)
        channel = await self.bot.fetch_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        await message.remove_reaction(payload.emoji, user)

        message_content, _ = NonPrintableEncoder.decode(message.content)

        await user.send(locale.format("editing_message", message=message_content))

        second_message = locale.send_content_of_new_message
        hidden_dict = {
            "guild_id": payload.guild_id,
            "channel_id": payload.channel_id,
            "message_id": payload.message_id,
            "tupper_id": metadata_dict["tupper_id"],
        }

        second_message_content = NonPrintableEncoder.encode(
            second_message, json.dumps(hidden_dict).encode()
        )

        await user.send(second_message_content)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.guild_id != config.guild:
            return

        # TODO check this strange bruh moment. need support custom emoji
        if (str(payload.emoji) != self.reaction_to_edit) and (
                str(payload.emoji) != self.reaction_to_remove
        ):
            return

        channel = await self.bot.fetch_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

        if message.content.find(hidden_header) <= -1:
            return

        message_content, hidden_bytes = NonPrintableEncoder.decode(message.content)
        metadata_dict = json.loads(hidden_bytes.decode())

        if "tupper_id" in metadata_dict:
            db_user = await User.get(discord_id=payload.user_id)
            if not db_user:
                return
            await self._remove_message(payload, db_user, metadata_dict)
            await self._create_edit_message(payload, db_user, metadata_dict)
        else:
            return

    async def _edit_tupper_message(self, new_message: discord.Message):
        message_with_metadata = None
        async for message in new_message.channel.history(
                before=new_message, limit=10, oldest_first=False
        ):
            print(message.content, message.content.find(hidden_header))
            if message.content.find(hidden_header) > -1:
                message_with_metadata = message
                break

        if not message_with_metadata:
            await new_message.reply(locale.nothing_to_edit)

            return

        _, hidden_bytes = NonPrintableEncoder.decode(message_with_metadata.content)
        metadata_dict: dict = json.loads(hidden_bytes.decode())

        if "nothing_to_edit" in metadata_dict:
            await new_message.reply(locale.nothing_to_edit)

            return
        # TODO dict check
        # TODO exception handler
        db_user = await User.get(discord_id=new_message.author.id)
        if not db_user:
            return

        tupper = await db_user.tuppes.filter(id=metadata_dict.get("tupper_id")).first()
        if not tupper:
            return

        hidden_data = {"tupper_id": tupper.id}
        message_content = NonPrintableEncoder.encode(
            new_message.content, json.dumps(hidden_data).encode()
        )

        # TODO we need to edit files or not?
        webhook = await self._get_webhook(metadata_dict.get("channel_id"))
        await webhook.edit_message(
            metadata_dict.get("message_id"), content=message_content
        )

        channel = await self.bot.fetch_channel(metadata_dict.get("channel_id"))
        message = await channel.fetch_message(metadata_dict.get("message_id"))

        hidden_data = {"nothing_to_edit": True}
        message_relpy = NonPrintableEncoder.encode(
            locale.format("message_edited", jump_url=message.jump_url), json.dumps(hidden_data).encode()
        )

        await new_message.reply(message_relpy)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # cut off bots and selfmessages

        if (message.author.id == self.bot.user.id) or message.author.bot:
            return

        db_user = await User.get(discord_id=message.author.id)
        if not db_user:
            return

        if message.channel.type == discord.ChannelType.private:
            await self._edit_tupper_message(message)
            return

        message_content = message.content.strip()

        tupper = None
        async for other_tupper in db_user.tuppers:
            if match := re.match(other_tupper.call_pattern, message_content):
                tupper = other_tupper
                message_content = match.groups(1)
                break

        if not tupper:
            return

        webhook = await self._get_webhook(message.channel.id)
        hidden_data = {"tupper_id": tupper.id}

        if len(message_content) == 0:
            return
        # TODO limit messages to 1800 with relpy
        # TODO await bot.process_commands(message)
        # Change to create custom ctx type with custom send and relpy system
        # Main idea it is create new child message and sent to function bot.process_commands
        # Not sure about of this variant but this code also not ideal...

        new_content = await handle_tupper_command(webhook, tupper, message_content)
        if new_content is not None:
            message_content = new_content

        message_content = NonPrintableEncoder.encode_dict(message_content, hidden_data)

        files_content = [
            await attachment.to_file(spoiler=attachment.is_spoiler())
            for attachment in message.attachments
        ]

        await webhook.send(
            message_content,
            username=tupper.name,
            avatar_url=tupper.image,
            files=files_content,
        )
        await message.delete()


async def setup(bot: "DiscoTupperBot"):
    await bot.add_cog(TupperMessageCog(bot))
