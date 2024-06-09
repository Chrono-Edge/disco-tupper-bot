from localization import locale

HELP = ("", locale.balance_desc)


async def handle(ctx):
    if ctx.command.argc != 0:
        return locale.format("wrong_usage", command_name=__name__.split(".")[-1], usage=HELP[0])
    
    return locale.format("current_balance", balance=ctx.tupper.balance)
