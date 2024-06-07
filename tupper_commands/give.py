from localization import locale
from utils.get_tupper_id import get_tupper_id
from database.models.item import Item
from database.models.tupper import Tupper

from tortoise.expressions import F

HELP = (locale.give_params, locale.give_desc)


async def handle(ctx):
    if ctx.command.argc not in (1, 2):
        return None

    tupper_id = await get_tupper_id(ctx.bot, ctx.message)
    if tupper_id is None:
        return locale.reference_message_not_found

    to_tupper = await Tupper.get(id=tupper_id)
    if not to_tupper:
        return locale.no_such_tupper

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

    item = await Item.filter(name=name, tupper_owner=to_tupper).first()
    if not item:
        await Item.create(name=name, quantity=quantity, tupper_owner=to_tupper)
    else:
        await Item.filter(id=item.id).update(quantity=F("quantity") + quantity)

    await ctx.log("- `{quantity}` `{name}`", quantity=quantity, name=name)

    return locale.format("successfully_gived", name=name, quantity=quantity)