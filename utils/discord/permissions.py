from typing import List

import discord.ext.commands


class Permissions:

    @staticmethod
    async def get_user_is_admin(admin_role_names: List[str], ctx: discord.ext.commands.Context) -> bool:

        if ctx.guild is None or ctx.author is None:
            raise ValueError("Context must be used within a guild and with an author.")

        admin_roles = [
            discord.utils.get(ctx.guild.roles, name=role_name)
            for role_name in admin_role_names
        ]

        admin_roles = [role for role in admin_roles if role is not None]

        user_roles = set(ctx.author.roles)
        return any(role in user_roles for role in admin_roles)
