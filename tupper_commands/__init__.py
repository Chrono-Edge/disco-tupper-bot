import os
import shlex
import string
import importlib
from collections import namedtuple

import discord
from loguru import logger

import config
from localization import locale
from utils.discord.get_webhook import get_webhook
from utils.encoding.non_printable import NonPrintableEncoder


class Context:
    def __init__(self, bot, tupper, message, command):
        self.bot = bot
        self.tupper = tupper
        self.message = message
        self.command = command

    async def log_other(self, tupper, label, **kwargs):
        # this is pure evil.....

        old_tupper = self.tupper

        try:
            self.tupper = tupper

            await self.log(label, **kwargs)
        finally:
            self.tupper = old_tupper

    async def log(self, label, **kwargs):
        text = "\n".join(map(lambda key: locale.format(key, value=kwargs[key]), kwargs))
        text = f"[{getattr(locale, label)}] {text}"

        await self.bot.discord_logger.send_log(label, **kwargs)

        try:
            # TODO why need try?
            webhook, thread = await get_webhook(self.bot, self.tupper.inventory_chat_id)
            if not webhook:
                return

            hidden_data = {
                "tupper_id": self.tupper.id,
                "author_id": self.message.author.id,
            }
            text = NonPrintableEncoder.encode_dict(text, hidden_data)

            await webhook.send(
                text,
                username=self.tupper.name,
                avatar_url=self.tupper.image,
                thread=thread,
                suppress_embeds=True,
            )
        except (
                discord.InvalidData,
                discord.HTTPException,
                discord.NotFound,
                discord.Forbidden,
        ) as e:
            logger.warning(f"Failed to log: {e}")


Command = namedtuple("Command", ["name", "args", "argc"])


def lat_to_cyr(c):
    try:
        return "абцдефгхижклмнопкрстуввхуз"[string.ascii_lowercase.index(c)]
    except ValueError:
        return "?"


class TupperCommands:
    def __init__(self, bot):
        self.bot = bot

        self.commands = {}
        self.help_lines = {}

    def register_command(self, name, handler, help="N/A"):
        self.commands[name] = handler
        self.commands[name[0]] = handler
        self.commands[lat_to_cyr(name[0])] = handler

        self.help_lines[name] = help

    def register_commands(self, path="tupper_commands"):
        for name in filter(lambda name: not name.startswith("__"), os.listdir(path)):
            name = name.split(".")[0]

            module = importlib.import_module(f"tupper_commands.{name}")

            self.register_command(name, module.handle, help=getattr(module, "HELP", "N/A"))

            logger.success(f"Registered tupper command: {name}")

        async def help(ctx):
            if locale.language == "en":
                buffer = ""

                for command in self.help_lines:
                    params, desc = self.help_lines[command]

                    command = (
                            "[" + command[0] + "|" + lat_to_cyr(command[0]) + "]" + command[1:]
                    )

                    if not params:
                        buffer += f"{command}: {desc}\n"
                    else:
                        buffer += f"{command} {params}: {desc}\n"

                return f"```{buffer.strip()}```"

            if ctx.command.argc == 0:
                buffer = locale.help_preline

                for command in self.help_lines:
                    buffer += f"- `{command}`, `{command[0]}`, `{lat_to_cyr(command[0])}`\n"

                buffer += locale.help_postline

                return buffer

            query = []
            for command in ctx.command.args:
                command = command.strip().lower()
                if command.startswith(config.prefixes):
                    command = command[1:]

                if command not in self.commands:
                    return locale.format("wrong_usage", command_name=command, usage="?")

                query.append(command)

            if not query:
                return locale.empty

            buffer = ""

            for command in self.help_lines:
                if command not in query and command[0] not in query and lat_to_cyr(command[0]) not in query:
                    continue

                params, desc = self.help_lines[command]

                buffer += f"{params}{desc}\n"

            return buffer.strip()

        self.register_command("help", help, help=(locale.help_params, locale.help_desc))

    async def handle_command(self, tupper, message, text):
        text = text.strip()

        if not text or not text.startswith(tuple(config.prefixes)):
            return None

        try:
            parts = shlex.split(text[1:])
        except ValueError:
            return None

        if len(parts) < 1 or len(parts) > 20:
            return None

        command = Command(name=parts[0].lower(), args=parts[1:], argc=len(parts) - 1)

        if command.name not in self.commands:
            return None

        # TODO remove hardcode
        if command.name not in ("help", "h", "х", "roll", "r", "р") and tupper.inventory_chat_id == 0:
            return locale.tupper_is_disabled

        return await self.commands[command.name](
            Context(bot=self.bot, tupper=tupper, message=message, command=command)
        )
