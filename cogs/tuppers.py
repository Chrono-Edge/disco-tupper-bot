from typing import TYPE_CHECKING

from utils.encoding.non_printable import NonPrintableEncoder

if TYPE_CHECKING:
    from bot import DiscoTupperBot

import discord
from discord.ext import commands
from config import logger


class TupperCog(commands.Cog):
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.id == self.bot.user.id:
            return
        logger.info(message.content)
        if message.content[:2] == "99":
            webhook = await message.channel.create_webhook(name=str(message.author.id))

            embed = discord.Embed(type="link")
            embed.set_author(name="Creator", )
            test_text = NonPrintableEncoder.encode(str(message.content[2:]), "HIDDEN TEXT".encode())
            await webhook.send(test_text, username="Test",
                               avatar_url="https://media.discordapp.net/attachments/738472141636501594/1245268256172933120/image.png?ex=665821f0&is=6656d070&hm=508f4a1c5645b655a30e07ecd49fd5976f169cbb6c206e457a95219b40f76967&=&format=webp&quality=lossless&width=534&height=532")

            print(message)
            await webhook.delete()
            message.content = message.content[2:]
            print(message.content)
            await self.bot.process_commands(message)

    @commands.command(name='test')
    async def test(self, ctx: discord.ext.commands.Context):
        await ctx.send("99 responce")


    @commands.command(name='get_info')
    async def get_mess_info(self, ch_id: int, mess_id: int):
        channel = await self.bot.fetch_channel(ch_id)
        message = await channel.fetch_message(mess_id)
        decode_text = NonPrintableEncoder.decode(message.content)
        logger.info(message.content)
        logger.info(decode_text.decode())

    @commands.hybrid_command(name="create_actor")
    async def create_actor(self, ctx, name: str):
        pass

    @commands.hybrid_command(name="remove_actor")
    async def remove_actor(self, ctx, name: str):
        pass

    @commands.hybrid_command(name="edit_actor")
    async def edit_actor(self, ctx, actor_name: str, parameter: str, value=""):
        parameter_list = ["name", "call_pattern", "avatar", "inventory_chat_id"]
        pass

    @commands.hybrid_command(name="set_actor_avatar")
    async def set_actor_avatar(self, ctx, member : discord.Member):
        pass

    @commands.hybrid_command(name="add_user_to_actor")
    async def add_user_to_actor(self, ctx):
        pass

    @commands.hybrid_command(name="remove_user_to_actor")
    async def remove_user_to_actor(self, ctx):
        pass


async def setup(bot: "DiscoTupperBot"):
    await bot.add_cog(TupperCog(bot))
