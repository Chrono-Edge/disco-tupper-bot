import re
import operator

from localization import locale
from database.models.attribute import Attribute

HELP = (locale.attributes_params, locale.attributes_desc)

OPS = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": lambda a, b: 0 if b == 0 else int(a / b),
}


async def handle(ctx):
    if ctx.command.argc not in (0, 1, 2, 3):
        return locale.format(
            "wrong_usage", command_name=__name__.split(".")[-1], usage=HELP[0]
        )

    if ctx.command.argc > 0:
        name = ctx.command.args[0].strip().upper()
        if not re.match(r"^[А-ЯA-Z]{2,3}$", name):
            return locale.illegal_attribute_name

        if ctx.command.argc == 1:
            if not await ctx.tupper.attrs.filter(name=name).exists():
                return locale.format("no_such_attribute", attribute_name=name)

            attr = await ctx.tupper.attrs.filter(name=name).first().values("value")

            return f"`{name}`: `{attr['value']}`"

        if ctx.command.argc == 3:
            if not await ctx.tupper.attrs.filter(name=name).exists():
                return locale.format("no_such_attribute", attribute_name=name)

            op = ctx.command.args[1].strip()

            if op not in OPS:
                return locale.format(
                    "wrong_usage", command_name=__name__.split(".")[-1], usage=HELP[0]
                )

            try:
                value = int(ctx.command.args[2])
            except ValueError:
                return locale.format(
                    "wrong_usage", command_name=__name__.split(".")[-1], usage=HELP[0]
                )

            attr = await ctx.tupper.attrs.filter(name=name).first().values("value")

            value = OPS[op](attr["value"], value)

            if value == attr["value"]:
                return locale.format("attribute_was_not_changed", attribute_name=name)

            await ctx.tupper.attrs.filter(name=name).update(value=value)

            await ctx.log(
                "log_attr_set",
                log_attr_name=name,
                log_attr_old_value=attr["value"],
                log_attr_new_value=value,
                log_jump_url=ctx.message.reference.jump_url
                if ctx.message.reference
                else ctx.message.jump_url,
            )

            return locale.format(
                "attribute_was_successfully_changed",
                attribute_name=name,
                value=value,
                old_value=attr["value"],
            )

        if ctx.command.args[1] in "Xx-":
            if not await ctx.tupper.attrs.filter(name=name).exists():
                return locale.format("no_such_attribute", attribute_name=name)

            attr = await ctx.tupper.attrs.filter(name=name).first().values("value")
            await ctx.tupper.attrs.filter(name=name).delete()

            await ctx.log(
                "log_attr_remove",
                log_attr_name=name,
                log_jump_url=ctx.message.reference.jump_url
                if ctx.message.reference
                else ctx.message.jump_url,
            )

            return locale.format(
                "attribute_was_successfully_removed", attribute_name=name
            )

        try:
            value = int(ctx.command.args[1])
        except ValueError:
            return locale.format(
                "wrong_usage", command_name=__name__.split(".")[-1], usage=HELP[0]
            )

        old_attr = await ctx.tupper.attrs.filter(name=name).first()
        if not old_attr:
            await ctx.log(
                "log_attr_set",
                log_attr_name=name,
                log_attr_new_value=value,
                log_jump_url=ctx.message.reference.jump_url
                if ctx.message.reference
                else ctx.message.jump_url,
            )

            await Attribute.create(owner=ctx.tupper, name=name, value=value)
        else:
            if old_attr.value == value:
                return locale.format("attribute_was_not_changed", attribute_name=name)

            await ctx.log(
                "log_attr_set",
                log_attr_name=name,
                log_attr_old_value=old_attr.value,
                log_attr_new_value=value,
                log_jump_url=ctx.message.reference.jump_url
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
