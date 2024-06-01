from discord.abc import Snowflake

from database.models.user import User


class UserRepository:
    """Repository class for handling CRUD operations with User objects."""

    @staticmethod
    async def create_user(discord_id: int) -> User:
        """
        Create a new user with the given Discord ID and username.

        Args:
            discord_id (Snowflake): The Discord ID of the user.
            username (str): The username of the user.

        Returns:
            User: The newly created user object.
        """
        user = await User.create(id=discord_id)
        return user

    @staticmethod
    async def get_or_create_user(discord_id: int) -> User:
        """
        Get or Create a user with the given Discord ID and username.

        Args:
            discord_id (Snowflake): The Discord ID of the user.
            username (str): The username of the user.

        Returns:
            User: The newly created user object.
        """

        user = await User.filter(id=discord_id).first()
        print(user)
        if not user:
            user = await User.create(id=discord_id)
        return user


    @staticmethod
    async def get_user_by_discord_id(discord_id: int) -> User:
        """
        Retrieve a user by their Discord ID.

        Args:
            discord_id (Snowflake): The Discord ID of the user to retrieve.

        Returns:
            User: The user object if found, else None.
        """
        user = await User.filter(id=discord_id).first()
        return user

    @staticmethod
    async def delete_user(discord_id: Snowflake):
        """
        Delete a user by their ID.

        Args:
            discord_id (int): The ID of the user to delete.
        """
        await User.filter(id=discord_id).delete()

    @staticmethod
    async def count_users() -> int:
        """
        Count the total number of users.

        Returns:
            int: The total number of users.
        """
        count = await User.all().count()
        return count

    @staticmethod
    async def get_all_users() -> list[User]:
        """
        Retrieve all users.

        Returns:
            list[User]: A list of all user objects.
        """
        users = await User.all()
        return users

    @staticmethod
    async def get_paginated_users(limit: int, offset: int) -> list[User]:
        """
        Retrieve a paginated list of users.

        Args:
            limit (int): The maximum number of users to retrieve.
            offset (int): The number of users to skip.

        Returns:
            list[User]: A list of user objects.
        """
        users = await User.all().limit(limit).offset(offset)
        return users
