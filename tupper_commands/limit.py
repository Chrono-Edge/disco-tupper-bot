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
        limit = int(ctx.command.args[1])
    except ValueError:
        return locale.format(
            "wrong_usage", command_name=__name__.split(".")[-1], usage=HELP[0]
        )

    attr = await ctx.tupper.attrs.filter(name=name).first()
    if not attr:
        return locale.format("no_such_attribute", attribute_name=name)

    await ctx.tupper.attrs.filter(id=attr.id).update(limit=limit)

    await ctx.log(
        "log_attr_set_limit",
        log_attr_name=name,
        log_attr_old_value=attr.limit,
        log_attr_new_value=limit,
        log_jump_url=ctx.message.reference.jump_url
        if ctx.message.reference
        else ctx.message.jump_url,
    )

    return locale.format(
        "successfully_set_limit", attribute_name=name, limit=limit, old_limit=attr.limit
    )
