import os
import shlex
import importlib
from collections import namedtuple

import config


class Context:
    def __init__(self, bot, tupper, message, command):
        self.bot = bot
        self.tupper = tupper
        self.message = message
        self.command = command

    async def log(self, text, **kwargs):
        channel = await self.bot.fetch_channel(self.tupper.inventory_chat_id)
        if channel:
            await channel.send(text.format(**kwargs))


Command = namedtuple("Command", ["name", "args", "argc"])


class TupperCommands:
    def __init__(self, bot):
        self.bot = bot

        self.commands = {}

    def register_command(self, name, handler, aliases=None):
        self.commands[name] = handler

        if not aliases:
            aliases = [name[0]]

        for name in aliases:
            self.commands[name] = handler

    def register_commands(self, path="tupper_commands"):
        for module in filter(lambda name: not name.startswith("__"), os.listdir(path)):
            module = module.split(".")[0]
            module = importlib.import_module(f"tupper_commands.{module}")

            self.register_command(module, module.handle)

    async def handle_command(self, tupper, message, text):
        text = text.strip()

        if not text or not text.startswith(tuple(config.prefixes)):
            return None

        try:
            parts = shlex.split(text[1:])
        except ValueError:
            return None

        if len(parts) < 1:
            return None

        command = Command(name=parts[0].lower(), args=parts[1:], argc=len(parts) - 1)

        if command.name not in self.commands:
            return None

        return await self.commands[command.name](
            Context(bot=self.bot, tupper=tupper, message=message, command=command)
        )
