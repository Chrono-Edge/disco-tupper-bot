from bot import bot

async def log(text, channel=bot.log_channel, **kwargs):
    text = text.format(**kwargs)

    if isinstance(channel, int):
        channel = await bot.fetch_channel(channel)

    await channel.send(text)
