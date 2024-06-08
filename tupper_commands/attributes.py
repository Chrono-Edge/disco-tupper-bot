import re

from localization import locale
from database.models.attribute import Attribute

HELP = (locale.attributes_params, locale.attributes_desc)


async def handle(ctx):
    if ctx.command.argc == 2:
        name = ctx.command.args[0].strip().upper()
        if not re.match(r"^[А-ЯA-Z]{2,3}$", name):
            return locale.illegal_attribute_name

        if ctx.command.args[1] in "Xx-":
            if not await ctx.tupper.attrs.filter(name=name).exists():
                return locale.format("no_such_attribute", attribute_name=name)

            attr = await ctx.tupper.attrs.filter(name=name).first().values("value")
            await ctx.tupper.attrs.filter(name=name).delete()

            await ctx.log(
                "A `{name}`: `{value}` -> X {jump_url}",
                name=name,
                value=attr["value"],
                jump_url=ctx.message.reference.jump_url
                if ctx.message.reference
                else ctx.message.jump_url,
            )

            return locale.format(
                "attribute_was_successfully_removed", attribute_name=name
            )

        try:
            value = int(ctx.command.args[1])
        except ValueError:
            return None

        old_attr = await ctx.tupper.attrs.filter(name=name).first()

        if not old_attr:
            await ctx.log(
                "A `{name}`: `{value}` {jump_url}",
                name=name,
                value=value,
                jump_url=ctx.message.reference.jump_url
                if ctx.message.reference
                else ctx.message.jump_url,
            )

            await Attribute.create(owner=ctx.tupper, name=name, value=value)
        else:
            if old_attr.value == value:
                return locale.format("attribute_was_not_changed", attribute_name=name)

            await ctx.log(
                "A `{name}`: `{old_value}` -> `{value}` {jump_url}",
                name=name,
                old_value=old_attr.value,
                value=value,
                jump_url=ctx.message.reference.jump_url
                if ctx.message.reference
                else ctx.message.jump_url,
            )

            await ctx.tupper.attrs.filter(id=old_attr.id).update(value=value)

        return locale.format(
            "attribute_was_successfully_changed",
            attribute_name=name,
            value=value,
            old_value=old_attr.value if old_attr else "X",
        )

    buffer = ""

    async for attr in ctx.tupper.attrs:
        buffer += f"`{attr.name}`: `{attr.value}`\n"

    if len(ctx.tupper.attrs) == 0:
        buffer += locale.empty

    return buffer
