from localization import locale
from utils.discord.get_tupper_id import get_tupper_id
from database.models.item import Item
from database.models.tupper import Tupper

from tortoise.exceptions import DoesNotExist
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

    if to_tupper.id == ctx.tupper.id:
        return locale.cannot_give_to_yourself

    name = ctx.command.args[0].strip().lower()

    if ctx.command.argc == 1:
        quantity = 1
    elif ctx.command.argc == 2:
        try:
            quantity = abs(int(ctx.command.args[1]))
        except ValueError:
            return None

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

    item = await Item.filter(name=name, tupper_owner=to_tupper).first()
    if not item:
        await Item.create(name=name, quantity=quantity, tupper_owner=to_tupper)
    else:
        await Item.filter(id=item.id).update(quantity=F("quantity") + quantity)

    await ctx.log(
        "log_give",
        log_item_name=name,
        log_quantity=quantity,
        log_receiver=to_tupper.name,
        log_jump_url=ctx.message.reference.jump_url,
    )
    await ctx.log_other(
        to_tupper,
        "log_incoming_item",
        log_item_name=name,
        log_quantity=quantity,
        log_sender=ctx.tupper.name,
        log_jump_url=ctx.message.reference.jump_url,
    )

    return locale.format(
        "successfully_gived",
        item_name=name,
        quantity=quantity,
        tupper_name=to_tupper.name,
    )
