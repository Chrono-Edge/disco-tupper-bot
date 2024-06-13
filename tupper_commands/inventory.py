from localization import locale
from database.models.item import Item

from tortoise.exceptions import DoesNotExist

HELP = (locale.inventory_params, locale.inventory_desc)


async def handle(ctx):
    buffer = ""

    if ctx.command.argc > 0:
        for name in ctx.command.args:
            name = name.strip().lower()

            try:
                item = await Item.get(name=name, tupper_owner=ctx.tupper)
            except DoesNotExist:
                return locale.format("unknown_item", item_name=name)
        
            if not item:
                return locale.format("unknown_item", item_name=name)
        
            if item.desc:
                buffer += f"`{item.name}` ({item.quantity}): `{item.desc}`\n"
            else:
                buffer += f"`{item.name}` ({item.quantity})\n"
        
        return buffer.rstrip()

    async for item in ctx.tupper.items:
        if item.desc:
            buffer += f"`{item.name}` ({item.quantity}): `{item.desc}`\n"
        else:
            buffer += f"`{item.name}` ({item.quantity})\n"

    if len(ctx.tupper.items) == 0:
        return locale.empty

    return buffer.rstrip()
