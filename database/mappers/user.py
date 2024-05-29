from database.models.user import User
from discord import Member

class UserMapper:
    @staticmethod
    def to_discord_member(user: User) -> Member:
        """
        Convert a database User object to a discord.Member object.
        This is a stub method and needs actual discord context to work.

        Args:
            user (User): The database user object.

        Returns:
            Member: The discord member object.
        """
        # This is just a placeholder example. Actual implementation may vary
        # depending on how you get the discord Member object from User data.
        member = Member
        member.name = user.username
        member.id = user.discord_id
        return member

    @staticmethod
    def from_discord_member(member: Member) -> User:
        """
        Convert a discord.Member object to a database User object.

        Args:
            member (Member): The discord member object.

        Returns:
            User: The database user object.
        """
        user = User(discord_id=member.id, username=member.name)
        return user