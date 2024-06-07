from localization import locale
from database.models.item import Item

from tortoise.expressions import F


async def handle(ctx):
    if not ctx.message.reference:
        return locale.reference_message_not_found
    
    if ctx.command.argc not in (1, 2):
        return None

    if ctx.command.argc >= 1:
        name = ctx.command.args[0].strip().lower()

    if ctx.command.argc == 2:
        try:
            quantity = abs(int(ctx.command.args[1]))
        except ValueError:
            return None
    else:
        quantity = 1

    item = await Item.filter(name=name, tupper_owner=ctx.tupper).first()
    if not item:
        await Item.create(name=name, quantity=quantity, tupper_owner=ctx.tupper)
    else:
        await Item.filter(id=item.id).update(quantity=F("quantity") + quantity)

    # TODO: log this to tupper.inventory_chat_id.
    
    return locale.format("successfully_obtained", name=name, quantity=quantity)
