from database.models.actor import Actor
import discord

class ActorMapper:

    @staticmethod
    def to_discord_embed(actor: Actor) -> discord.Embed:
        """
        Convert an Actor model instance to a Discord Embed object.

        Args:
            actor (Actor): The Actor instance to convert.

        Returns:
            discord.Embed: The resulting Discord Embed object.
        """
        embed = discord.Embed(
            title=actor.name,
            description=f"Balance: {actor.balance}",
            timestamp=actor.created_at
        )
        embed.set_image(url=actor.image)
        embed.add_field(name="Call Pattern", value=actor.call_pattern)
        embed.add_field(name="Owner ID", value=actor.owner_id)
        embed.add_field(name="Created at:", value=actor.created_at)
        embed.set_footer(text=f"Actor ID: {actor.id}")
        return embed