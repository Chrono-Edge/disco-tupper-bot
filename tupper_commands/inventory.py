from localization import locale

HELP = ("", locale.inventory_desc)


async def handle(ctx):
    if ctx.command.argc != 0:
        return locale.format("wrong_usage", command_name=__name__.split(".")[-1], usage=HELP[0])
    
    buffer = ""

    async for item in ctx.tupper.items:
        if item.desc:
            buffer += f"`{item.name}` ({item.quantity}): `{item.desc}`\n"
        else:
            buffer += f"`{item.name}` ({item.quantity})\n"

    if len(ctx.tupper.items) == 0:
        buffer += locale.empty

        return buffer
    
    return buffer
