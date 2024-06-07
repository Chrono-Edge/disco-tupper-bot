from localization import locale
from utils.get_tupper_id import get_tupper_id
from database.models.tupper import Tupper

from tortoise.expressions import F


async def handle(ctx):
    if ctx.command.argc != 1:
        return None

    tupper_id = await get_tupper_id(ctx.bot, ctx.message)
    if tupper_id is None:
        return locale.reference_message_not_found

    to_tupper = await Tupper.get(id=tupper_id)
    if not to_tupper:
        return locale.no_such_tupper

    try:
        amount = abs(int(ctx.command.args[0]))
    except ValueError:
        return None

    try:
        amount = abs(int(amount))
    except ValueError:
        return None

    if amount > ctx.tupper.balance:
        return locale.format("balance_is_too_low", need=amount, have=ctx.tupper.balance)

    new_balance = ctx.tupper.balance - amount
    await Tupper.filter(id=ctx.tupper.id).update(balance=new_balance)
    await Tupper.filter(id=to_tupper).update(balance=F("balance") + amount)

    return locale.format("current_balance", balance=new_balance)
