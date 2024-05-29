import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot import DiscoTupperBot

from discord.ext import commands


class DicesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='roll', aliases=['dice'])
    async def roll_dice(self, ctx, number_of_dice: int = 1, number_of_sides: int = 6):

        """
        Roll a dice.
        
        Args:
        number_of_dice (int, optional): Number of dice to roll. Defaults to 1.
        number_of_sides (int, optional): Number of sides on each die. Defaults to 6.
        """

        if number_of_dice <= 0 or number_of_sides <= 0:
            await ctx.send(f"Number of dice and sides must be positive integers.")
            return

        if number_of_dice > 10 or number_of_sides > 100:
            await ctx.send("Please keep the number of dice and sides reasonable.")
            return

        if number_of_sides % 2 != 0:
            await ctx.send("Number of sides on the dice must be even.")
            return

        rolls = [random.randint(1, number_of_sides) for _ in range(number_of_dice)]
        total = sum(rolls)
        rolls_str = ', '.join(map(str, rolls))

        await ctx.send(f"You rolled: {rolls_str}. Total: {total}")


async def setup(bot: "DiscoTupperBot"):
    await bot.add_cog(DicesCog(bot))
