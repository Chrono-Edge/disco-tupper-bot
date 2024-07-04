import asyncio
import copy
from collections import namedtuple
from enum import Enum

from discord import MessageType
from discord import MessageType
from discord.ext import commands
import discord
import json
import string
from builtins import str
from typing import TYPE_CHECKING

import config
from database.models.tupper import Tupper
from database.models.user import User
from utils.messages.tupper_parser import MessageUtilsForTuppers
from utils.sign import Sign
from utils.discord.message_split import TextFormatterSplit
from utils.encoding.non_printable import NonPrintableEncoder
from utils.encoding.non_printable import HEADER
from utils.discord.get_webhook import get_webhook
from utils.tupper_template import TupperCallPattern, PatternType
from localization import locale

if TYPE_CHECKING:
    from bot import DiscoTupperBot


class TupperMessageCog(commands.Cog):
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot = bot
        self.reaction_to_edit = config.values.get("bot.reaction_to_edit")
        self.reaction_to_remove = config.values.get("bot.reaction_to_remove")
        self.text_splitter = TextFormatterSplit()

    async def _get_webhook(
            self, channel_id: int
    ) -> tuple[discord.Webhook, discord.Thread]:
        return await get_webhook(self.bot, channel_id)

    async def _remove_message(
            self, payload: discord.RawReactionActionEvent, db_user: User, metadata_dict
    ):
        """Remove message on reaction"""
        if str(payload.emoji) != self.reaction_to_remove:
            return
        tupper = await db_user.tuppers.filter(id=metadata_dict["tupper_id"]).first()
        if not tupper:
            return
        webhook, thread = await self._get_webhook(payload.channel_id)
        await webhook.delete_message(payload.message_id, thread=thread)

    async def _create_edit_message(
            self, payload: discord.RawReactionActionEvent, db_user: User, metadata_dict
    ):
        """Create message in personal chat to edit message"""
        if str(payload.emoji) != self.reaction_to_edit:
            return

        tupper = await db_user.tuppers.filter(id=metadata_dict["tupper_id"]).first()

        if not tupper:
            return

        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        channel = await guild.fetch_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

        await message.remove_reaction(payload.emoji, member)

        message_content, message_hidden_dict = NonPrintableEncoder.decode_dict(
            message.content
        )

        if message_hidden_dict is None or "sign" in message_hidden_dict:
            # TODO hiden text return
            return

        second_message = locale.send_content_of_new_message

        hidden_dict = {
            "guild_id": payload.guild_id,
            "channel_id": payload.channel_id,
            "message_id": payload.message_id,
            "tupper_id": metadata_dict["tupper_id"],
        }

        second_message_content = NonPrintableEncoder.encode_dict(
            second_message, hidden_dict
        )

        if member.is_on_mobile() or ("```" in message_content):
            await member.send(locale.format("editing_message", message=f"{'v' * 16}"))
            await member.send(message_content)
            await member.send(f"```{'^' * 16}```\n" + second_message_content)
        else:
            await member.send(locale.format("editing_message", message=message_content))
            await member.send(second_message_content)

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

        if message.content.find(HEADER) <= -1:
            return

        message_content, metadata_dict = NonPrintableEncoder.decode_dict(
            message.content
        )

        if metadata_dict is not None and "tupper_id" in metadata_dict:
            db_user = await User.get(discord_id=payload.user_id)
            if not db_user:
                return
            await self._remove_message(payload, db_user, metadata_dict)
            await self._create_edit_message(payload, db_user, metadata_dict)
        else:
            return

    async def _edit_tupper_message(self, new_message: discord.Message):
        """Edit message from personal chat"""
        message_with_metadata = None

        async for message in new_message.channel.history(
                before=new_message, limit=10, oldest_first=False
        ):
            # find message with metadata to edit
            if message.content.find(HEADER) > -1:
                message_with_metadata = message
                break

        if not message_with_metadata:
            await new_message.reply(locale.nothing_to_edit)
            return

        _, metadata_dict = NonPrintableEncoder.decode_dict(
            message_with_metadata.content
        )

        if "nothing_to_edit" in metadata_dict:
            # If message already edited
            await new_message.reply(locale.nothing_to_edit)
            return

        # TODO dict check
        # TODO exception handler
        db_user = await User.filter(discord_id=new_message.author.id).first()
        if not db_user:
            return

        tupper = await db_user.tuppers.filter(id=metadata_dict.get("tupper_id")).first()
        if not tupper:
            return

        message_hidden_data = {
            "tupper_id": tupper.id,
            "author_id": new_message.author.id,
        }

        message_content = NonPrintableEncoder.encode_dict(
            new_message.content, message_hidden_data
        )

        # TODO we need to edit files or not?
        channel = await self.bot.fetch_channel(metadata_dict.get("channel_id"))
        if channel.guild.id != config.guild:
            return

        webhook, thread = await self._get_webhook(channel.id)

        await webhook.edit_message(
            metadata_dict.get("message_id"),
            content=message_content,
            thread=thread,
        )

        channel = await self.bot.fetch_channel(metadata_dict.get("channel_id"))
        message = await channel.fetch_message(metadata_dict.get("message_id"))

        hidden_data = {"nothing_to_edit": True}
        message_relpy = NonPrintableEncoder.encode(
            locale.format("message_edited", jump_url=message.jump_url),
            json.dumps(hidden_data).encode(),
        )

        await new_message.reply(message_relpy)

    async def _handle_message(self, tupper, original_message, message_content):
        # TODO limit messages to 1800 with relpy
        # TODO await bot.process_commands(message)
        # Change to create custom ctx type with custom send and relpy system
        # Main idea it is create new child message and sent to function bot.process_commands
        # Not sure about of this variant but this code also not ideal...

        message_content = message_content.strip()
        if not message_content:
            return False

        webhook, thread = await self._get_webhook(original_message.channel.id)
        hidden_data = {"tupper_id": tupper.id, "author_id": original_message.author.id}

        command_content = await self.bot.tupper_commands.handle_command(
            tupper, original_message, message_content
        )

        if command_content:
            message_content = command_content
            files_content = []
            hidden_data["sign"] = Sign.sign(
                message_content, tupper.id, original_message.channel.id
            )
            message_content = NonPrintableEncoder.encode_dict(
                message_content, hidden_data
            )
        else:
            relpy_string_header = None

            if original_message.reference:
                channel = await self.bot.fetch_channel(original_message.reference.channel_id)
                relpy_message = await channel.fetch_message(
                    original_message.reference.message_id
                )
                _, relpy_dict = NonPrintableEncoder.decode_dict(relpy_message.content)

                # check tupper message or not
                if relpy_dict:
                    if "tupper_id" in relpy_dict and "author_id" in relpy_dict:
                        relpy_member = await self.bot.fetch_user(
                            relpy_dict["author_id"]
                        )
                        actor = await Tupper.filter(id=relpy_dict["tupper_id"]).first()
                        relpy_string_header = f"> `{actor.name}` ({relpy_member.mention}) - {relpy_message.jump_url}\n"
                else:
                    relpy_string_header = (
                        f"> {relpy_message.author.mention} - {relpy_message.jump_url}\n"
                    )

            message_content = NonPrintableEncoder.encode_dict(
                message_content, hidden_data
            )

            if relpy_string_header:
                message_content = relpy_string_header + message_content

            files_content = [
                await attachment.to_file(spoiler=attachment.is_spoiler())
                for attachment in original_message.attachments
            ]

        if len(message_content) > 2000:
            original_message, _ = NonPrintableEncoder.decode_dict(message_content)
            list_messages = self.text_splitter.format_text(original_message)
            list_messages = [
                NonPrintableEncoder.encode_dict(
                    splited_message,
                    hidden_data.update(
                        {
                            "sign": Sign.sign(
                                splited_message, tupper.id, original_message.channel.id
                            )
                        }
                    )
                    if "sign" in hidden_data
                    else hidden_data,
                )
                for splited_message in list_messages
            ]
            for message_to_send in list_messages:
                await webhook.send(
                    message_to_send,
                    username=tupper.name,
                    avatar_url=tupper.image,
                    files=files_content,
                    thread=thread,
                )
        else:
            await webhook.send(
                message_content,
                username=tupper.name,
                avatar_url=tupper.image,
                files=files_content,
                thread=thread,
            )

        return True

    async def _on_message(self, message: discord.Message):
        """parse on message"""
        # cut off bots and selfmessages
        # if channel is private
        if (message.author.id == self.bot.user.id) or message.author.bot:
            return

        if message.type == MessageType.chat_input_command:
            return

        if message.channel.type == discord.ChannelType.private:
            return await self._edit_tupper_message(message)

        if message.guild.id != config.guild:
            return

        # take user form database by discord id
        db_user = await User.filter(discord_id=message.author.id).first()
        if not db_user:
            return

        # message content
        message_content = message.content.strip()
        if not message_content:
            return

        tupper_message_worker = MessageUtilsForTuppers(db_user, message_content)

        if not await tupper_message_worker.is_message_for_tuppers():
            return

        await tupper_message_worker.find_all_patterns_on_lines()

        await tupper_message_worker.text_fill_left_pattern()
        await tupper_message_worker.text_fill_right_pattern()
        await tupper_message_worker.text_fill_right_and_left()

        message_lines = tupper_message_worker.message_lines
        # format message if this has start pattern
        for i, pattern in enumerate(tupper_message_worker.pattern_on_lines):
            if not pattern:
                continue
            if not pattern.is_none() and not pattern.is_text() and not pattern.is_left_and_right():
                message_lines[i] = pattern.format_text(message_lines[i])

        previous_pattern = TupperCallPattern(None)
        pattern_left_right = TupperCallPattern(None)
        tupper_message = ""

        message_task = []

        for pattern, message_line in zip(tupper_message_worker.pattern_on_lines, message_lines):
            if pattern.is_none():
                continue

            if previous_pattern.tupper.id != pattern.tupper.id:
                # start another tupper
                message_task.append(self._handle_message(previous_pattern.tupper, message, tupper_message))
                tupper_message = ""
                pattern_left_right = TupperCallPattern(None)

            if pattern.is_only_right():
                tupper_message += f"{message_line}\n"
                message_task.append(self._handle_message(pattern.tupper, message, tupper_message))

                tupper_message = ""
                previous_pattern = pattern
                continue
            elif pattern.is_left_and_right():
                if pattern.text_startswith(message_line) and pattern.text_endswith(message_line):
                    message_temp = pattern.format_text(message_line)

                    tupper_message += f"{message_temp}\n"
                    message_task.append(self._handle_message(pattern.tupper, message, tupper_message))

                    tupper_message = ""
                    previous_pattern = pattern
                    continue
                elif pattern.text_startswith(message_line):
                    message_temp = pattern.format_text(message_line)
                    tupper_message += f"{message_temp}\n"

                    pattern_left_right = pattern
                    previous_pattern = pattern
                    continue
                elif (pattern_left_right == pattern) and pattern.text_endswith(message_line):
                    message_temp = pattern.format_text(message_line)

                    tupper_message += f"{message_temp}\n"
                    message_task.append(self._handle_message(pattern.tupper, message, tupper_message))

                    tupper_message = ""

                    pattern_left_right = TupperCallPattern(None)
                    previous_pattern = pattern
                    continue
            elif not pattern.is_text():
                message_task.append(self._handle_message(previous_pattern.tupper, message, tupper_message))
                tupper_message = ""
                pattern_left_right = TupperCallPattern(None)

            tupper_message += f"{message_line}\n"
            previous_pattern = pattern

        message_task.append(self._handle_message(previous_pattern.tupper, message, tupper_message))

        if message_task:
            for task in message_task:
                await task
                await asyncio.sleep(0)
        await message.delete()
        return

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        await self._on_message(message)

    @commands.Cog.listener()
    async def on_message_edit(self, before_message, after_message: discord.Message):
        await self._on_message(after_message)


async def setup(bot: "DiscoTupperBot"):
    await bot.add_cog(TupperMessageCog(bot))
