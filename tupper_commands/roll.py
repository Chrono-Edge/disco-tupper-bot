from utils.dices import roll_dices
from localization import locale

HELP = (locale.roll_params, locale.roll_desc)


async def handle(ctx):
    if ctx.command.argc < 1:
        return

    vars = {}
    async for attr in ctx.tupper.attrs:
        vars[attr.name] = attr.value

    return roll_dices(" ".join(ctx.command.args), vars=vars)
