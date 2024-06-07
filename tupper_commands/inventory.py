from localization import locale

HELP = ("", locale.inventory_desc)


async def handle(ctx):
    buffer = locale.format("inventory_of", tupper_name=ctx.tupper.name)

    buffer += "\n"

    async for item in ctx.tupper.items:
        buffer += f"`{item.name}` ({item.quantity})\n"

    if len(ctx.tupper.items) == 0:
        buffer += locale.empty

        return buffer
    
    return buffer
