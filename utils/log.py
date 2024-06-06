from bot import bot

async def log(text, **kwargs):
    text = text.format(**kwargs)

    await bot.log_channel.send(text)
