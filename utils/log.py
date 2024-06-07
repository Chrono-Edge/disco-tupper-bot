from bot import bot

async def log(text, channel=bot.log_channel, **kwargs):
    text = text.format(**kwargs)

    await channel.send(text)
