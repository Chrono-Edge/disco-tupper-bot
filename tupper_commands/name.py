from localization import locale
from database.models.item import Item

from tortoise.exceptions import DoesNotExist

HELP = (locale.name_params, locale.name_desc)


async def handle(ctx):
    if ctx.command.argc != 2:
        return locale.format(
            "wrong_usage", command_name=__name__.split(".")[-1], usage=HELP[0]
        )

    name = ctx.command.args[0].strip().lower()
    new_name = ctx.command.args[1].strip()

    try:
        item = await Item.get(name=name, tupper_owner=ctx.tupper)
    except DoesNotExist:
        return locale.format("unknown_item", item_name=name)

    if not item:
        return locale.format("unknown_item", item_name=name)
    
    if await Item.filter(name=new_name, tupper_owner=ctx.tupper).exists():
        return locale.format("name_already_in_use", item_name=name)

    await Item.filter(id=item.id).update(name=new_name)

    await ctx.log(
        "log_item_rename",
        log_item_name=name,
        log_attr_old_value=name,
        log_attr_new_value=new_name,
        log_jump_url=ctx.message.reference.jump_url
        if ctx.message.reference
        else ctx.message.jump_url,
    )

    return locale.format("successfully_renamed", old_item_name=name, item_name=new_name)
