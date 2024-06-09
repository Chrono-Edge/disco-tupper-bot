from localization import locale
from utils.discord.get_tupper_id import get_tupper_id
from database.models.tupper import Tupper

from tortoise.expressions import F

HELP = (locale.send_params, locale.send_desc)


async def handle(ctx):
    if ctx.command.argc != 1:
        return locale.format("wrong_usage", command_name=__name__.split(".")[-1], usage=HELP[0])

    tupper_id = await get_tupper_id(ctx.bot, ctx.message)
    if tupper_id is None:
        return locale.reference_message_not_found

    to_tupper = await Tupper.get(id=tupper_id)
    if not to_tupper:
        return locale.no_such_tupper
    
    if ctx.tupper.id == to_tupper.id:
        return locale.cannot_send_to_yourself

    try:
        amount = abs(int(ctx.command.args[0]))
    except ValueError:
        return locale.format("wrong_usage", command_name=__name__.split(".")[-1], usage=HELP[0])

    if amount > ctx.tupper.balance:
        return locale.format("balance_is_too_low", need=amount, have=ctx.tupper.balance)

    new_balance = ctx.tupper.balance - amount
    await Tupper.filter(id=ctx.tupper.id).update(balance=new_balance)
    await Tupper.filter(id=to_tupper.id).update(balance=F("balance") + amount)

    await ctx.log(
        "log_send",
        log_quantity=amount,
        log_receiver=to_tupper.name,
        log_old_balance=ctx.tupper.balance,
        log_new_balance=new_balance,
        log_jump_url=ctx.message.reference.jump_url
    )
    await ctx.log_other(
        to_tupper,
        "log_incoming_balance",
        log_quantity=amount,
        log_sender=ctx.tupper.name,
        log_old_balance=to_tupper.balance,
        log_new_balance=to_tupper.balance + amount,
        log_jump_url=ctx.message.reference.jump_url
    )

    return locale.format(
        "sent_to", amount=amount, tupper_name=to_tupper.name, balance=new_balance
    )
