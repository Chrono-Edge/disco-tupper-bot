from localization import locale


async def handle(ctx):
    buffer = locale.format("inventory_of", tupper_name=ctx.tupper.name)

    if len(ctx.tupper.items) == 0:
        buffer += locale.empty

        return buffer

    async for item in ctx.tupper.items:
        buffer += f"`{item.name}` ({item.quantity})\n"

    return buffer
