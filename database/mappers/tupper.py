import discord

from database.models.tupper import Tupper


class TupperMapper:
    @staticmethod
    def to_discord_embed(tupper: Tupper) -> discord.Embed:
        """
        Convert an Tupper model instance to a Discord Embed object.

        Args:
            tupper (Tupper): The Tupper instance to convert.

        Returns:
            discord.Embed: The resulting Discord Embed object.
        """

        embed = discord.Embed(
            title=tupper.name,
            description=f"Balance: {tupper.balance}",
            timestamp=tupper.created_at,
        )
        embed.set_image(url=tupper.image)
        embed.add_field(name="Call Pattern", value=tupper.call_pattern)
        embed.add_field(name="Created at:", value=tupper.created_at)
        embed.set_footer(text=f"Actor ID: {tupper.id}")
        return embed
