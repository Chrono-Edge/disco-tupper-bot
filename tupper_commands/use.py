from localization import locale
from database.models.item import Item

from tortoise.expressions import F

HELP = (locale.use_params, locale.use_desc)


async def handle(ctx):
    if ctx.command.argc not in (1, 2):
        return None

    name = ctx.command.args[0].strip().lower()

    if ctx.command.argc == 1:
        quantity = 1
    elif ctx.command.argc == 2:
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

    await ctx.log(
        "X `{quantity}` `{name}` {jump_url}",
        quantity=quantity,
        name=name,
        jump_url=ctx.message.reference.jump_url
        if ctx.message.reference
        else ctx.message.jump_url,
    )

    return locale.format("successfully_used", item_name=name, quantity=quantity)
