import re

from localization import locale
from database.models.attribute import Attribute


async def handle(ctx):
    if ctx.command.argc == 2:
        name = ctx.command.args[0].strip().lower()
        if not re.match(r"^[а-яa-z]{2,3}$", name):
            return locale.illegal_attribute_name

        try:
            value = int(ctx.command.args[1])
        except ValueError:
            return None

        if not await ctx.tupper.attrs.filter(name=name).exists():
            await Attribute.create(owner=ctx.tupper, name=name, value=value)
        else:
            await ctx.tupper.attrs.filter(name=name).update(value=value)

        return locale.attribute_was_successfully_changed

    buffer = ""

    async for attr in ctx.tupper.attrs:
        buffer += f"`{attr.name}`: `{attr.value}`\n"

    if len(ctx.tupper.attrs) == 0:
        buffer += locale.empty

    return buffer
