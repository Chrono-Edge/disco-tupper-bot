import re

from localization import locale
from database.models.attribute import Attribute

HELP = (locale.limit_params, locale.limit_desc)


async def handle(ctx):
    if ctx.command.argc != 2:
        return locale.format(
            "wrong_usage", command_name=__name__.split(".")[-1], usage=HELP[0]
        )

    name = ctx.command.args[0].strip().upper()
    if not re.match(r"^[А-ЯA-Z]{2,3}$", name):
        return locale.illegal_attribute_name

    if not await ctx.tupper.attrs.filter(name=name).exists():
        return locale.format("no_such_attribute", attribute_name=name)

    try:
        if ctx.command.args[1] in "-Xx":
            limit = 0
        else:
            limit = abs(int(ctx.command.args[1]))
    except ValueError:
        return locale.format(
            "wrong_usage", command_name=__name__.split(".")[-1], usage=HELP[0]
        )

    attr = await ctx.tupper.attrs.filter(name=name).first()
    if not attr:
        return locale.format("no_such_attribute", attribute_name=name)

    await ctx.tupper.attrs.filter(id=attr.id).update(value=min(attr.value, limit), limit=limit)

    await ctx.log(
        "log_attr_set_limit",
        log_attr_name=name,
        log_attr_old_value='X' if attr.limit == 0 else attr.limit,
        log_attr_new_value='X' if limit == 0 else limit,
        log_jump_url=ctx.message.reference.jump_url
        if ctx.message.reference
        else ctx.message.jump_url,
    )

    return locale.format(
        "successfully_set_limit", attribute_name=name, limit='X' if limit == 0 else limit, old_limit='X' if attr.limit == 0 else attr.limit
    )
