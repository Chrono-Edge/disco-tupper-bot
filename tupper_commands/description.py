from localization import locale
from database.models.item import Item

from tortoise.exceptions import DoesNotExist

HELP = (locale.desc_params, locale.desc_desc)


async def handle(ctx):
    if ctx.command.argc != 2:
        return locale.format(
            "wrong_usage", command_name=__name__.split(".")[-1], usage=HELP[0]
        )

    name = ctx.command.args[0].strip().lower()
    desc = ctx.command.args[1].strip()

    try:
        item = await Item.get(name=name, tupper_owner=ctx.tupper)
    except DoesNotExist:
        return locale.format("unknown_item", item_name=name)

    if not item:
        return locale.format("unknown_item", item_name=name)

    await Item.filter(id=item.id).update(desc=desc)

    await ctx.log(
        "log_desc_set",
        log_item_name=name,
        log_attr_old_value=item.desc,
        log_attr_new_value=desc,
        log_jump_url=ctx.message.reference.jump_url
        if ctx.message.reference
        else ctx.message.jump_url,
    )

    return locale.format("successfully_set_desc", item_name=name, desc=desc)
