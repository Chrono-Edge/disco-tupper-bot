from localization import locale


async def handle(ctx):
    return locale.format("current_balance", balance=ctx.tupper.balance)
