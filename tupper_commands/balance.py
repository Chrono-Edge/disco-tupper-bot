from localization import locale

HELP = ("", locale.balance_desc)


async def handle(ctx):
    return locale.format("current_balance", balance=ctx.tupper.balance)
