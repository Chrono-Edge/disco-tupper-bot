import json
from builtins import str
from typing import TYPE_CHECKING

import config
from database.models.actor import Actor
from database.models.user import User
from utils.encoding.non_printable import NonPrintableEncoder
from utils.encoding.non_printable import HEADER

hidden_header = HEADER

if TYPE_CHECKING:
    from bot import DiscoTupperBot

import discord
from discord.ext import commands
from config import logger
from database.repositories.user import UserRepository
from database.repositories.actor import ActorRepository


class TupperCog(commands.Cog):
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot = bot
        self.reaction_to_edit = config.values.get("bot.reaction_to_edit")
        self.reaction_to_remove = config.values.get("bot.reaction_to_remove")

    async def _get_webhook(self, channel_id: int):
        # TODO exception if limit of used webhooks
        channel = await self.bot.fetch_channel(channel_id)
        webhooks_list = await channel.webhooks()
        webhook = None
        for in_webhook in webhooks_list:
            if in_webhook.name == str(self.bot.user.id):
                webhook = in_webhook
        if not webhook:
            webhook = await channel.create_webhook(name=str(self.bot.user.id))
        return webhook

    async def _remove_message(self, payload: discord.RawReactionActionEvent, db_user: User, metadata_dict):
        if str(payload.emoji) != self.reaction_to_remove:
            return
        actor: Actor = await db_user.actors.filter(id=metadata_dict["actor_id"]).first()
        if not actor:
            return
        webhook = await self._get_webhook(payload.channel_id)
        await webhook.delete_message(payload.message_id)

    async def _create_edit_message(self, payload: discord.RawReactionActionEvent, db_user: User, metadata_dict):
        if str(payload.emoji) != self.reaction_to_edit:
            return
        actor: Actor = await db_user.actors.filter(id=metadata_dict["actor_id"]).first()
        if not actor:
            return

        user = await self.bot.fetch_user(payload.user_id)
        channel = await self.bot.fetch_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        await message.remove_reaction(payload.emoji, user)

        message_content, hidden_bytes = NonPrintableEncoder.decode(message.content)

        await user.send(f"Editing message:```{message_content}```")

        second_message = "Please send me the new content of the message here:"
        hidden_dict = {"guild_id": payload.guild_id, "channel_id": payload.channel_id, "message_id": payload.message_id,
                       "actor_id": metadata_dict["actor_id"]}

        second_message_content = NonPrintableEncoder.encode(second_message, json.dumps(hidden_dict).encode())

        await user.send(second_message_content)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.guild_id != config.guild:
            return

        # TODO check this strange bruh moment. need support custom emoji
        if (str(payload.emoji) != self.reaction_to_edit) and (str(payload.emoji) != self.reaction_to_remove):
            return

        channel = await self.bot.fetch_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

        if message.content.find(hidden_header) <= -1:
            return

        message_content, hidden_bytes = NonPrintableEncoder.decode(message.content)
        metadata_dict = json.loads(hidden_bytes.decode())

        if "actor_id" in metadata_dict:
            db_user = await UserRepository.get_user_by_discord_id(payload.user_id)
            if not db_user:
                return
            await self._remove_message(payload, db_user, metadata_dict)
            await self._create_edit_message(payload, db_user, metadata_dict)
        else:
            return

    async def _edit_tupper_message(self, new_message: discord.Message):
        message_with_metadata = None
        async for message in new_message.channel.history(before=new_message, limit=10, oldest_first=False):
            print(message.content, message.content.find(hidden_header))
            if message.content.find(hidden_header) > -1:
                message_with_metadata = message
                break

        if not message_with_metadata:
            await new_message.reply("Nothing to edit!")
            return

        ___, hidden_bytes = NonPrintableEncoder.decode(message_with_metadata.content)
        metadata_dict: dict = json.loads(hidden_bytes.decode())

        if "nothing_to_edit" in metadata_dict:
            await new_message.reply("Nothing to edit!")
            return
        # TODO dict check
        # TODO exception handler
        db_user = await UserRepository.get_user_by_discord_id(new_message.author.id)
        if not db_user:
            return

        actor: Actor = await db_user.actors.filter(id=metadata_dict.get("actor_id")).first()
        if not actor:
            return

        hidden_data = {"actor_id": actor.id}
        message_content = NonPrintableEncoder.encode(new_message.content, json.dumps(hidden_data).encode())

        # TODO we need to edit files or not?
        webhook = await self._get_webhook(metadata_dict.get("channel_id"))
        await webhook.edit_message(metadata_dict.get("message_id"), content=message_content)

        channel = await self.bot.fetch_channel(metadata_dict.get("channel_id"))
        message = await channel.fetch_message(metadata_dict.get("message_id"))

        hidden_data = {"nothing_to_edit": True}
        message_relpy = NonPrintableEncoder.encode(f"Message edited: {message.jump_url}",
                                                   json.dumps(hidden_data).encode())

        await new_message.reply(message_relpy)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # cut off bots and selfmessages

        if (message.author.id == self.bot.user.id) or message.author.bot:
            return

        db_user = await UserRepository.get_user_by_discord_id(message.author.id)
        if not db_user:
            return

        if message.channel.type == discord.ChannelType.private:
            print("private")
            await self._edit_tupper_message(message)
            return

        start_message = message.content[:256]
        first_word = start_message.split()[0]

        actor: Actor = await db_user.actors.filter(call_pattern=first_word).first()
        if not actor:
            return

        webhook = await self._get_webhook(message.channel.id)

        hidden_data = {"actor_id": actor.id}
        message_content = message.content.split(actor.call_pattern, 1)[1].strip()
        if len(message_content) == 0:
            return
        # TODO limit messages to 1800 with relpy

        message_content = NonPrintableEncoder.encode(message_content, json.dumps(hidden_data).encode())

        files_content = [await attachment.to_file(spoiler=attachment.is_spoiler()) for attachment in
                         message.attachments]

        await webhook.send(message_content, username=actor.name, avatar_url=actor.image, files=files_content)
        await message.delete()

    @commands.command(name='test')
    async def test(self, ctx: discord.ext.commands.Context):
        await ctx.send("99 responce")

    @commands.command(name='get_info')
    async def get_mess_info(self, ctx, ch_id: int, mess_id: int):
        channel = await self.bot.fetch_channel(ch_id)
        message = await channel.fetch_message(mess_id)
        decode_text = NonPrintableEncoder.decode(message.content)
        logger.info(message.content)
        logger.info(decode_text.decode())
        await ctx.send(f"Hidden text {decode_text}")

    @commands.hybrid_command(name="create_actor")
    @commands.has_any_role(*config.player_roles)
    async def create_actor(self, ctx: discord.ext.commands.Context, name: str, call_pattern: str):
        user = await UserRepository.get_or_create_user(ctx.author.id)
        actor = await ActorRepository.create_actor(name=name, call_pattern=call_pattern,
                                                   image=config.values.get("actor.default_avatar_url"))
        await user.actors.add(actor)
        logger.debug(user)
        logger.debug(actor)
        await ctx.send("OK!")

    @commands.hybrid_command(name="remove_actor")
    @commands.has_any_role(*config.player_roles)
    async def remove_actor(self, ctx, name: str):
        pass

    @commands.hybrid_command(name="edit_actor")
    @commands.has_any_role(*config.player_roles)
    async def edit_actor(self, ctx, actor_name: str, parameter: str, value=""):
        parameter_list = ["name", "call_pattern", "inventory_chat_id"]
        pass

    @commands.hybrid_command(name="set_actor_avatar")
    @commands.has_any_role(*config.player_roles)
    async def set_actor_avatar(self, ctx, member: discord.Member):
        pass

    @commands.hybrid_command(name="add_user_to_actor")
    @commands.has_any_role(*config.player_roles)
    async def add_user_to_actor(self, ctx):
        pass

    @commands.hybrid_command(name="remove_user_to_actor")
    @commands.has_any_role(*config.player_roles)
    async def remove_user_to_actor(self, ctx):
        pass


async def setup(bot: "DiscoTupperBot"):
    await bot.add_cog(TupperCog(bot))
