from localization import locale
from database.models.item import Item

from tortoise.expressions import F

HELP = (locale.take_params, locale.take_desc)


async def handle(ctx):
    if not ctx.message.reference:
        return locale.reference_message_not_found

    if ctx.command.argc not in (1, 2, 3):
        return locale.format(
            "wrong_usage", command_name=__name__.split(".")[-1], usage=HELP[0]
        )

    name = ctx.command.args[0].strip().lower()

    if ctx.command.argc >= 2:
        try:
            quantity = abs(int(ctx.command.args[1]))
        except ValueError:
            return locale.format(
                "wrong_usage", command_name=__name__.split(".")[-1], usage=HELP[0]
            )
    else:
        quantity = 1

    if ctx.command.argc == 3:
        desc = ctx.command.args[2].strip()
    else:
        desc = None

    item = await Item.filter(name=name, tupper_owner=ctx.tupper).first()
    if not item:
        await Item.create(
            name=name,
            quantity=quantity,
            tupper_owner=ctx.tupper,
            desc="" if desc is None else desc,
        )
    else:
        await Item.filter(id=item.id).update(quantity=F("quantity") + quantity)

        if desc is not None:
            await Item.filter(id=item.id).update(desc=desc)

    if desc is not None:
        await ctx.log(
            "log_incoming_item",
            log_item_name=name,
            log_quantity=quantity,
            log_desc=desc,
            log_jump_url=ctx.message.reference.jump_url,
        )
    else:
        await ctx.log(
            "log_incoming_item",
            log_item_name=name,
            log_quantity=quantity,
            log_jump_url=ctx.message.reference.jump_url,
        )

    return locale.format("successfully_obtained", item_name=name, quantity=quantity)
