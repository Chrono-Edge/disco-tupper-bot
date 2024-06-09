from localization import locale
from database.models.item import Item

from tortoise.exceptions import DoesNotExist
from tortoise.expressions import F

HELP = (locale.use_params, locale.use_desc)


async def handle(ctx):
    if ctx.command.argc not in (1, 2, 3):
        return locale.format("wrong_usage", command_name=__name__.split(".")[-1], usage=HELP[0])

    name = ctx.command.args[0].strip().lower()

    if ctx.command.argc == 1:
        quantity = 1
    elif ctx.command.argc >= 2:
        try:
            quantity = abs(int(ctx.command.args[1]))
        except ValueError:
            return locale.format("wrong_usage", command_name=__name__.split(".")[-1], usage=HELP[0])
        
    desc = None
    if ctx.command.argc == 3:
        desc = ctx.command.args[2]

    try:
        item = await Item.get(name=name, tupper_owner=ctx.tupper)
    except DoesNotExist:
        return locale.format("unknown_item", item_name=name)
    
    if not item:
        return locale.not_enough_items

    if item.quantity < quantity:
        return locale.not_enough_items

    if quantity == item.quantity:
        await Item.filter(id=item.id).delete()
    else:
        await Item.filter(id=item.id).update(quantity=F("quantity") - quantity)

    await ctx.log(
        "log_use",
        log_item_name=name,
        log_quantity=quantity,
        log_jump_url=ctx.message.reference.jump_url
        if ctx.message.reference
        else ctx.message.jump_url,
    )

    if desc:
        return locale.format("successfully_used_desc", item_name=name, quantity=quantity, desc=desc)
    
    return locale.format("successfully_used", item_name=name, quantity=quantity)
