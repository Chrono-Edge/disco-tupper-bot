from collections import namedtuple
from enum import Enum

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
from utils.tupper_template import get_template_start, split_template
from localization import locale

if TYPE_CHECKING:
    from bot import DiscoTupperBot


class PatternType(Enum):
    NONE = 0
    LEFT_AND_RIGHT = 1
    LEFT_ONLY = 2
    RIGHT_ONLY = 3


class TupperCallPattern:
    left_pattern_part = ""
    right_pattern_part = ""
    tupper = None
    pattern = ""
    pattern_type = PatternType.NONE

    def __init__(self, pattern: str, tupper: Tupper):
        if not pattern:
            left_pattern_part = ""
            right_pattern_part = ""
        else:
            left_pattern_part, right_pattern_part = split_template(tupper.call_pattern)
        if not tupper:
            temp = namedtuple("dummy", "id")
            self.tupper = temp(-1)
        else:
            self.tupper = tupper

        self.pattern = pattern

        self.left_pattern_part = left_pattern_part
        self.right_pattern_part = right_pattern_part

        if left_pattern_part and right_pattern_part:
            self.pattern_type = PatternType.LEFT_AND_RIGHT
        elif left_pattern_part and not right_pattern_part:
            self.pattern_type = PatternType.LEFT_ONLY
        elif not left_pattern_part and right_pattern_part:
            self.pattern_type = PatternType.RIGHT_ONLY

    def __hash__(self):
        return f"{self.pattern}-{self.tupper.id}"

    def __repr__(self):
        return f"TupperCallPattern({self.pattern}, {self.tupper.id}, [{self.left_pattern_part}|{self.right_pattern_part}])"

    def is_only_left(self) -> bool:
        return self.pattern_type == PatternType.LEFT_ONLY

    def is_only_right(self) -> bool:
        return self.pattern_type == PatternType.RIGHT_ONLY

    def is_left_and_right(self) -> bool:
        return self.pattern_type == PatternType.LEFT_AND_RIGHT

    def is_none(self) -> bool:
        return self.pattern_type == PatternType.NONE

    def text_startswith(self, text: str) -> bool:
        return text.startswith(self.left_pattern_part) and (self.left_pattern_part != "")

    def text_endswith(self, text: str) -> bool:
        return text.endswith(self.right_pattern_part) and (self.right_pattern_part != "")

    def format_text(self, text):
        if self.text_startswith(text):
            text = text[len(self.left_pattern_part):].lstrip()
        if self.text_endswith(text):
            text = text[:len(text) - len(self.right_pattern_part)].rstrip()
        return text


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

    async def _handle_message(self, tupper, message, message_content):
        # TODO limit messages to 1800 with relpy
        # TODO await bot.process_commands(message)
        # Change to create custom ctx type with custom send and relpy system
        # Main idea it is create new child message and sent to function bot.process_commands
        # Not sure about of this variant but this code also not ideal...

        webhook, thread = await self._get_webhook(message.channel.id)
        hidden_data = {"tupper_id": tupper.id, "author_id": message.author.id}

        command_content = await self.bot.tupper_commands.handle_command(
            tupper, message, message_content
        )

        if command_content:
            message_content = command_content
            files_content = []
            hidden_data["sign"] = Sign.sign(
                message_content, tupper.id, message.channel.id
            )
            message_content = NonPrintableEncoder.encode_dict(
                message_content, hidden_data
            )
        else:
            relpy_string_header = None

            if message.reference:
                channel = await self.bot.fetch_channel(message.reference.channel_id)
                relpy_message = await channel.fetch_message(
                    message.reference.message_id
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
                for attachment in message.attachments
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
                                splited_message, tupper.id, message.channel.id
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

    async def _on_message(self, message: discord.Message):
        """parse on message"""
        # cut off bots and selfmessages

        if (message.author.id == self.bot.user.id) or message.author.bot:
            return

        # take user form database by discord id
        db_user = await User.filter(discord_id=message.author.id).first()
        if not db_user:
            return

        # if channel is private
        if message.channel.type == discord.ChannelType.private:
            await self._edit_tupper_message(message)
            return

        if message.guild.id != config.guild:
            return

        # message content
        message_content = message.content.strip()
        if not message_content:
            return

        call_patterns_l: list[TupperCallPattern] = []
        call_patterns_r: list[TupperCallPattern] = []
        call_patterns_lr: list[TupperCallPattern] = []

        async for tupper in db_user.tuppers:
            # TODO move this info in database... like left part, right part and pattern_type
            # TODO charlist_filter

            pattern_to_add = TupperCallPattern(pattern=tupper.call_pattern, tupper=tupper)
            if pattern_to_add.pattern_type == PatternType.LEFT_ONLY:
                call_patterns_l.append(pattern_to_add)
            elif pattern_to_add.pattern_type == PatternType.RIGHT_ONLY:
                call_patterns_r.append(pattern_to_add)
            elif pattern_to_add.pattern_type == PatternType.LEFT_AND_RIGHT:
                call_patterns_lr.append(pattern_to_add)

        first_pattern_l = None
        first_pattern_r = None
        first_pattern_lr = None

        for call_pattern in call_patterns_l:
            if call_pattern.text_startswith(message_content):
                first_pattern_l = True

        for call_pattern in call_patterns_r:
            if call_pattern.text_endswith(message_content):
                first_pattern_r = True

        for call_pattern in call_patterns_lr:
            if call_pattern.text_startswith(message_content) or call_pattern.text_endswith(message_content):
                first_pattern_lr = True

        # if message not started from template we ignore this message
        if not first_pattern_l and not first_pattern_r and not first_pattern_lr:
            return

        # split message per line to check
        message_per_line = message_content.split("\n")

        # fill with patterns
        patterns_per_line: list[TupperCallPattern] = [TupperCallPattern("", tupper=None)] * len(message_per_line)
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
                if line.startswith(right_left_pattern.left_pattern_part) or line.endswith(
                        right_left_pattern.right_pattern_part):
                    patterns_per_line[i] = right_left_pattern
                    # not set tupper_per_line. we need find right part in text later...
                    break

        # only left template
        current_left_pattern = None
        for i, pattern in enumerate(patterns_per_line):
            if pattern.is_only_left():
                current_left_pattern = pattern
            elif (pattern.is_left_and_right() or pattern.is_none()) and not tupper_per_line[i] and current_left_pattern:
                tupper_per_line[i] = current_left_pattern.tupper
                patterns_per_line[i] = current_left_pattern
            else:
                current_left_pattern = None
                continue

        # only right template
        for i, pattern in enumerate(patterns_per_line):
            if pattern.is_only_right():
                tupper_per_line[i] = pattern.tupper
                for step_back in range(i - 1, -1, -1):
                    temp_pattern = patterns_per_line[step_back]
                    if (temp_pattern.is_left_and_right() or temp_pattern.is_none()) and not tupper_per_line[step_back]:
                        tupper_per_line[step_back] = pattern.tupper
                        patterns_per_line[step_back] = pattern
                    elif temp_pattern.is_only_right() or temp_pattern.is_only_left():
                        break
                    else:
                        continue

        # left and right
        current_left_and_right_pattern = None
        start_index = -1
        for i, pattern in enumerate(patterns_per_line):
            if (pattern.is_left_and_right() or pattern.is_none()) and not tupper_per_line[i]:
                if not current_left_and_right_pattern:
                    if pattern.text_startswith(message_per_line[i]):
                        current_left_and_right_pattern = pattern
                        start_index = i
                elif pattern == current_left_and_right_pattern:
                    if pattern.text_endswith(message_per_line[i]):
                        # end of left and right pattern
                        for index_to_set in range(start_index, i + 1):
                            patterns_per_line[index_to_set] = pattern
                            tupper_per_line[index_to_set] = pattern.tupper
                        current_left_and_right_pattern = None
                        start_index = -1
                elif pattern.is_none():
                    continue
                else:
                    current_left_and_right_pattern = None
                    start_index = -1
            else:
                current_left_and_right_pattern = None
                start_index = -1

        for i, pattern in enumerate(patterns_per_line):
            if not pattern:
                continue
            message_per_line[i] = pattern.format_text(message_per_line[i])

        last_tupper = tupper_per_line[0]
        tupper_message = ""

        for tupper, message_line in zip(tupper_per_line, message_per_line):
            if tupper is None:
                continue
            if tupper != last_tupper:
                await self._handle_message(last_tupper, message, tupper_message)
                tupper_message = ""
                last_tupper = tupper

            tupper_message += f"{message_line}\n"

        await self._handle_message(last_tupper, message, tupper_message)
        await message.delete()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        await self._on_message(message)

    @commands.Cog.listener()
    async def on_message_edit(self, before_message, after_message: discord.Message):
        await self._on_message(after_message)


async def setup(bot: "DiscoTupperBot"):
    await bot.add_cog(TupperMessageCog(bot))
