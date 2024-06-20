import copy
from collections import namedtuple
from enum import Enum

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

        user = await self.bot.fetch_user(payload.user_id)
        channel = await self.bot.fetch_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        await message.remove_reaction(payload.emoji, user)

        message_content, message_hidden_dict = NonPrintableEncoder.decode_dict(
            message.content
        )

        if message_hidden_dict is None or "sign" in message_hidden_dict:
            return

        await user.send(locale.format("editing_message", message=message_content))

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
        print(message.type)
        print(message.channel.type)
        if message.type == MessageType.chat_input_command:
            return

        if message.channel.type == discord.ChannelType.private:
            return await self._edit_tupper_message(message)

        if message.guild.id != config.guild:
            return

        if (message.author.id == self.bot.user.id) or message.author.bot:
            return

        # take user form database by discord id
        db_user = await User.filter(discord_id=message.author.id).first()
        if not db_user:
            return

        # message content
        message_content = message.content.strip()
        if not message_content:
            return

        call_patterns_l: list[TupperCallPattern] = []
        call_patterns_r: list[TupperCallPattern] = []
        call_patterns_lr: list[TupperCallPattern] = []

        async for tupper in db_user.tuppers:
            pattern_to_add = TupperCallPattern(tupper)
            if not all(c in message_content for c in pattern_to_add.charlist):
                continue

            if pattern_to_add.pattern_type == PatternType.LEFT_ONLY:
                call_patterns_l.append(pattern_to_add)
            elif pattern_to_add.pattern_type == PatternType.RIGHT_ONLY:
                call_patterns_r.append(pattern_to_add)
            elif pattern_to_add.pattern_type == PatternType.LEFT_AND_RIGHT:
                call_patterns_lr.append(pattern_to_add)

        first_pattern_l = None
        first_pattern_r = None
        first_pattern_lr = None

        # Find only left patterns
        for call_pattern in call_patterns_l:
            if call_pattern.text_startswith(message_content):
                first_pattern_l = True

        # Find only right patterns
        for call_pattern in call_patterns_r:
            if call_pattern.text_endswith(message_content):
                first_pattern_r = True

        # Find left with right patterns
        for call_pattern in call_patterns_lr:
            if call_pattern.text_startswith(message_content) or call_pattern.text_endswith(message_content):
                first_pattern_lr = True

        # if message not started from template we ignore this message
        if not first_pattern_l and not first_pattern_r and not first_pattern_lr:
            return

        # split message per line to check
        message_per_line = message_content.split("\n")

        # fill with patterns
        patterns_per_line: list[TupperCallPattern] = [TupperCallPattern(None)] * len(message_per_line)
        # fill with selected tuppers
        tupper_per_line: list[Tupper] = [None] * len(message_per_line)

        # find possible patterns
        for i, line in enumerate(message_per_line):
            # if left and right in one line this full one actor per line
            for right_left_pattern in call_patterns_lr:
                if right_left_pattern.text_startswith(line) and right_left_pattern.text_endswith(line):
                    patterns_per_line[i] = right_left_pattern
                    tupper_per_line[i] = right_left_pattern.tupper
                    break

            if not patterns_per_line[i].is_none():
                continue

            # only right text<
            for right_pattern in call_patterns_r:
                if right_pattern.text_endswith(line):
                    patterns_per_line[i] = right_pattern
                    tupper_per_line[i] = right_pattern.tupper
                    break

            if not patterns_per_line[i].is_none():
                continue

            # only left
            for left_pattern in call_patterns_l:
                if left_pattern.text_startswith(line):
                    patterns_per_line[i] = left_pattern
                    tupper_per_line[i] = left_pattern.tupper

            if not patterns_per_line[i].is_none():
                continue

            # right and left set to end. If some strange man set >text and text< and >text< template....

            for right_left_pattern in call_patterns_lr:
                if right_left_pattern.text_startswith(line) or right_left_pattern.text_endswith(line):
                    patterns_per_line[i] = right_left_pattern
                    tupper_per_line[i] = right_left_pattern.tupper

        for dddd in patterns_per_line:
            print(f"pf\t", dddd)

        # only left template
        current_left_pattern = None
        for i, pattern in enumerate(patterns_per_line):
            if pattern.is_only_left():
                current_left_pattern = pattern
                continue
            elif not current_left_pattern:
                continue
            elif pattern.is_none():
                copy_pattern = copy.deepcopy(current_left_pattern)
                copy_pattern.pattern_type = PatternType.TEXT
                patterns_per_line[i] = copy_pattern
            else:
                current_left_pattern = None
                continue

        # only right template
        for i, pattern in enumerate(patterns_per_line):
            if pattern.is_none() or pattern.is_left_and_right():
                continue

            if pattern.is_only_right():
                # go back for find all strings
                for step_back in range(i - 1, -1, -1):
                    step_back_pattern = patterns_per_line[step_back]
                    print(step_back, step_back_pattern, step_back_pattern.is_left_and_right(),
                          step_back_pattern.is_none())
                    if step_back_pattern.is_left_and_right() or step_back_pattern.is_none():
                        copy_pattern = copy.deepcopy(pattern)
                        copy_pattern.pattern_type = PatternType.TEXT
                        patterns_per_line[step_back] = copy_pattern
                    elif step_back_pattern.is_only_right() or step_back_pattern.is_only_left():
                        break

        # left and right
        current_left_and_right_pattern = None
        start_index = -1
        for i, pattern in enumerate(patterns_per_line):
            if pattern.is_left_and_right() or pattern.is_none():
                # if we get only left and right or none pattern
                if not current_left_and_right_pattern:
                    if pattern.text_startswith(message_per_line[i]):
                        current_left_and_right_pattern = pattern
                        start_index = i
                elif pattern == current_left_and_right_pattern:
                    if pattern.text_endswith(message_per_line[i]):
                        # we find the end go back to set for text!
                        for index_to_set in range(start_index + 1, i + 1):
                            print("old one", patterns_per_line[index_to_set])
                            copy_pattern = copy.deepcopy(pattern)
                            copy_pattern.pattern_type = PatternType.TEXT
                            patterns_per_line[index_to_set] = copy_pattern
                            print("new one", patterns_per_line[index_to_set])

                            tupper_per_line[index_to_set] = pattern.tupper

                        # End work with current pattern
                        current_left_and_right_pattern = None
                        start_index = -1
                elif pattern.is_none():
                    continue
                else:
                    # if we catch another patterns
                    current_left_and_right_pattern = None
                    start_index = -1
            else:
                # if we catch another pattern type
                current_left_and_right_pattern = None
                start_index = -1

        # format message if this has start pattern
        for i, pattern in enumerate(patterns_per_line):
            if not pattern:
                continue
            if not pattern.is_none() and not pattern.is_text():
                message_per_line[i] = pattern.format_text(message_per_line[i])

        previous_pattern = TupperCallPattern(None)
        tupper_message = ""

        message_task = []

        for dddd in patterns_per_line:
            print(f"pfin\t", dddd)

        for pattern, message_line in zip(patterns_per_line, message_per_line):
            if pattern.is_none():
                continue
            print(pattern, message_line)
            print(previous_pattern.tupper.id != pattern.tupper.id, pattern.is_only_right())

            if previous_pattern.tupper.id != pattern.tupper.id:
                # start another tupper
                message_task.append(self._handle_message(previous_pattern.tupper, message, tupper_message))
                tupper_message = ""

            if pattern.is_only_right():
                tupper_message += f"{message_line}\n"
                message_task.append(self._handle_message(pattern.tupper, message, tupper_message))
                tupper_message = ""
                previous_pattern = pattern
                continue
            elif not pattern.is_text():
                message_task.append(self._handle_message(previous_pattern.tupper, message, tupper_message))
                tupper_message = ""

            tupper_message += f"{message_line}\n"
            previous_pattern = pattern

        message_task.append(self._handle_message(previous_pattern.tupper, message, tupper_message))
        await message.delete()
        if message_task:
            for task in message_task:
                await task

        return

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        await self._on_message(message)

    @commands.Cog.listener()
    async def on_message_edit(self, before_message, after_message: discord.Message):
        await self._on_message(after_message)


async def setup(bot: "DiscoTupperBot"):
    await bot.add_cog(TupperMessageCog(bot))
