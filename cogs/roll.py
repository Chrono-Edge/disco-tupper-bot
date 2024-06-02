from discord.ext import commands

from utils.dices import Dices


class RollCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='roll', aliases=['r'])
    async def roll_dice(self, ctx, text: str):
        dices = Dices(text)

        try:
            dices.roll()
        except (ValueError, SyntaxError, NameError) as e:
            await ctx.send(str(e))

            return
        except ZeroDivisionError:
            await ctx.send('Попытка деления на ноль.')

            return

        await ctx.send(f'{ctx.author.display_name} бросает {dices}.')


async def setup(bot):
    await bot.add_cog(RollCog(bot))
