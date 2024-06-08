from utils.encoding.non_printable import NonPrintableEncoder
from utils.encoding.non_printable import HEADER


async def get_tupper_id(bot, message):
    if not message.reference:
        return None

    channel = await bot.fetch_channel(message.reference.channel_id)
    if not channel:
        return None

    message = await channel.fetch_message(message.reference.message_id)
    if not message:
        return None

    if message.content.find(HEADER) <= -1:
        return None

    _, metadata_dict = NonPrintableEncoder.decode_dict(message.content)

    if "tupper_id" not in metadata_dict:
        return None

    return int(metadata_dict["tupper_id"])
