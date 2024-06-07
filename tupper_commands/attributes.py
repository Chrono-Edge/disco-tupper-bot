import re

from localization import locale
from database.models.attribute import Attribute

HELP = (locale.attributes_params, locale.attributes_desc)


async def handle(ctx):
    if ctx.command.argc == 2:
        name = ctx.command.args[0].strip().upper()
        if not re.match(r"^[А-ЯA-Z]{2,3}$", name):
            return locale.illegal_attribute_name

        if ctx.command.args[1] == "-":
            await ctx.tupper.attrs.filter(name=name).delete()

            return locale.attribute_was_successfully_removed

        try:
            value = int(ctx.command.args[1])
        except ValueError:
            return None

        if not await ctx.tupper.attrs.filter(name=name).exists():
            await ctx.log(
                "`{name}`: `{value}` {jump_url}",
                name=name,
                value=value,
                jump_url=ctx.message.reference.jump_url
                if ctx.message.reference
                else ctx.message.jump_url,
            )

            await Attribute.create(owner=ctx.tupper, name=name, value=value)
        else:
            old_attr = await ctx.tupper.attrs.get(name=name)

            await ctx.log(
                "`{name}`: `{old_value}` -> `{value}` {jump_url}",
                name=name,
                old_value=old_attr.value,
                value=value,
                jump_url=ctx.message.reference.jump_url
                if ctx.message.reference
                else ctx.message.jump_url,
            )

            await ctx.tupper.attrs.filter(name=name).update(value=value)

        return locale.attribute_was_successfully_changed

    buffer = ""

    async for attr in ctx.tupper.attrs:
        buffer += f"`{attr.name}`: `{attr.value}`\n"

    if len(ctx.tupper.attrs) == 0:
        buffer += locale.empty

    return buffer
