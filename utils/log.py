from bot import bot
from utils.tupper_command import get_webhook
from utils.encoding.non_printable import NonPrintableEncoder

async def log(text, channel=bot.log_channel, **kwargs):
    text = text.format(**kwargs)

    if isinstance(channel, int):
        channel = await bot.fetch_channel(channel)

    await channel.send(text)

async def log_webhook(tupper, author_id, text, **kwargs):
    webhook, _ = await get_webhook(bot, tupper.inventory_chat_id)

    await webhook.send(
        NonPrintableEncoder.encode_dict(text.format(**kwargs), {"tupper_id": tupper.id, "author_id": author_id}),
        username=tupper.name,
        avatar_url=tupper.image
    )
