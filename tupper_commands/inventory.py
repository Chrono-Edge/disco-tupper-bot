from localization import locale
from database.models.item import Item

from tortoise.exceptions import DoesNotExist

HELP = (locale.inventory_params, locale.inventory_desc)


async def handle(ctx):
    if ctx.command.argc not in (0, 1):
        return locale.format(
            "wrong_usage", command_name=__name__.split(".")[-1], usage=HELP[0]
        )

    if ctx.command.argc == 1:
        name = ctx.command.args[0].strip().lower()

        try:
            item = await Item.get(name=name, tupper_owner=ctx.tupper)
        except DoesNotExist:
            return locale.format("unknown_item", item_name=name)
        
        if not item:
            return locale.format("unknown_item", item_name=name)
        
        if item.desc:
            return f"`{item.name}` ({item.quantity}): `{item.desc}`"
        
        return f"`{item.name}` ({item.quantity})"

    buffer = ""

    async for item in ctx.tupper.items:
        if item.desc:
            buffer += f"`{item.name}` ({item.quantity}): `{item.desc}`\n"
        else:
            buffer += f"`{item.name}` ({item.quantity})\n"

    if len(ctx.tupper.items) == 0:
        buffer += locale.empty

        return buffer

    return buffer
