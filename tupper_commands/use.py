from localization import locale
from database.models.item import Item

from tortoise.expressions import F


async def handle(ctx):
    if ctx.command.argc not in (1, 2):
        return None

    if ctx.command.argc == 1:
        name = ctx.command.args[0].strip().lower()
        quantity = 1
    elif ctx.command.argc == 2:
        name = ctx.command.args[0].strip().lower()
        try:
            quantity = abs(int(ctx.command.args[1]))
        except ValueError:
            return None

    item = await Item.get(name=name, tupper_owner=ctx.tupper)
    if not item:
        return locale.not_enough_items

    if item.quantity < quantity:
        return locale.not_enough_items

    if quantity == item.quantity:
        await Item.filter(id=item.id).delete()
    else:
        await Item.filter(id=item.id).update(quantity=F("quantity") - quantity)

    await ctx.log("X `{quantity}` `{name}`", quantity=quantity, name=name)

    return locale.format("successfully_used", name=name, quantity=quantity)
