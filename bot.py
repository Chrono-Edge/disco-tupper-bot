import traceback

import discord
from discord.ext import commands
from tortoise import Tortoise

import config
from config import logger

logger.info("Starting DiscoTupperBot")

prefixes = config.values.get("bot.prefixes")


class DiscoTupperBot(commands.Bot):
    def __init__(self) -> None:
        # Forward all arguments, and keyword-only arguments to commands.Bot
        super().__init__(
            intents=self.setup_intents(),
            command_prefix=commands.when_mentioned_or(*prefixes),  # type: ignore
        )
        if config.debug_guild:
            self.debug_guild = discord.Object(config.debug_guild)

    @staticmethod
    def setup_intents():
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        intents.messages = True
        return intents

    initial_extensions = config.values.get("bot.initial_extensions")

    async def setup_hook(self) -> None:
        logger.info("Bot initialisation...")
        for extension in self.initial_extensions:
            await self.load_extension(f'cogs.{extension}')
            logger.success(f"Loaded extension: {extension}")

        # logger.warning("Commands synchronization")
        # This copies the global commands over to your guild.
        guild = self.debug_guild

        self.tree.copy_global_to(guild=guild)
        if await self.tree.sync():
            logger.success("Commands synced!")

    async def on_ready(self):
        self.remove_command("help")
        logger.info(
            f"Logged in as: {self.user.name} - {self.user.id} Version: {discord.__version__}\n"
        )
        await self.change_presence(status=discord.Status.dnd)
        logger.success("Successfully loaded, the initialization of the modules...")

    async def on_error(self, interaction, *args, **kwargs):
        await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)
        error = traceback.format_exc()
        error_msg = (
            f"\ninteraction:\n{interaction}\n\nargs:\n{args}\nkwargs:\n{kwargs}\nerror:\n{error}"
        )
        logger.exception(error_msg)

    # Here you are overriding the default start method and write your own code.
    async def start(self, *args, **kwargs) -> None:
        await super().start(*args, **kwargs)

    @staticmethod
    async def init_tortoise(self):
        logger.info("Initializing Tortoise...")
        await Tortoise.init(
            db_url='sqlite://db.sqlite3',
            modules={'models': ['database.models.user', 'database.models.actor', 'database.models.item',
                                'database.models.item_log']},
        )
        logger.info("Tortoise initialized")
        await Tortoise.generate_schemas()


bot = DiscoTupperBot()
