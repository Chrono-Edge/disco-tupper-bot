from utils.dices import roll_dices
from localization import locale

HELP = (locale.roll_params, locale.roll_desc)


async def handle(ctx):
    if ctx.command.argc < 1:
        return locale.format(
            "wrong_usage", command_name=__name__.split(".")[-1], usage=HELP[0]
        )

    vars = {}
    async for attr in ctx.tupper.attrs:
        vars[attr.name] = attr.value

    roll = roll_dices(" ".join(ctx.command.args), vars=vars)

    await ctx.bot.discord_logger.send_log(
        "log_roll",
        log_author=ctx.message.author.name,
        log_tupper_name=ctx.tupper.name,
        log_roll_result=roll,
        log_jump_url=ctx.message.jump_url,
    )

    return roll
