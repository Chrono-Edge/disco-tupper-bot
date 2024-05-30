import json
from typing import TYPE_CHECKING

import config
from database.models.actor import Actor
from utils.encoding.non_printable import NonPrintableEncoder

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

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # cut off bots and selfmessages
        print(message.content)
        if (message.author.id == self.bot.user.id) or message.author.bot:
            return

        # TODO move to chache
        roles = [discord.utils.get(message.guild.roles, name=role_name) for role_name in config.player_roles]
        has_role = False

        for user_role in message.author.roles:
            if has_role:
                break
            if user_role in roles:
                has_role = True
        if not has_role:
            return

        db_user = await UserRepository.get_user_by_discord_id(message.author.id)
        if not db_user:
            return

        start_message = message.content[:256]
        first_word = start_message.split()[0]

        actor: Actor = await db_user.actors.filter(call_pattern=first_word).first()
        if not actor:
            return

        webhooks_list = await message.channel.webhooks()
        webhook = None
        for in_webhook in webhooks_list:
            if in_webhook.name == str(self.bot.user.id):
                webhook = in_webhook
        if not webhook:
            webhook = await message.channel.create_webhook(name=str(self.bot.user.id))

        hidden_data = {"actor_id": actor.id}
        parts = message.content.split(actor.call_pattern, 1)

        message_content = NonPrintableEncoder.encode(parts[1].lstrip(), json.dumps(hidden_data).encode())
        print(message_content.encode(), len(message_content))
        await webhook.send(message_content, username=actor.name, avatar_url=actor.image)

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
        print(config.values.get("bot.defalut_avatar_url"))
        user = await UserRepository.get_or_create_user(ctx.author.id)
        actor = await ActorRepository.create_actor(name=name, call_pattern=call_pattern,
                                                   image=config.values.get("bot.defalut_avatar_url"))
        await user.actors.add(actor)
        logger.debug(user)
        logger.debug(actor)
        await ctx.send("OK!")
        pass

    @commands.hybrid_command(name="remove_actor")
    async def remove_actor(self, ctx, name: str):
        pass

    @commands.hybrid_command(name="edit_actor")
    async def edit_actor(self, ctx, actor_name: str, parameter: str, value=""):
        parameter_list = ["name", "call_pattern", "avatar", "inventory_chat_id"]
        pass

    @commands.hybrid_command(name="set_actor_avatar")
    async def set_actor_avatar(self, ctx, member: discord.Member):
        pass

    @commands.hybrid_command(name="add_user_to_actor")
    async def add_user_to_actor(self, ctx):
        pass

    @commands.hybrid_command(name="remove_user_to_actor")
    async def remove_user_to_actor(self, ctx):
        pass


async def setup(bot: "DiscoTupperBot"):
    await bot.add_cog(TupperCog(bot))
