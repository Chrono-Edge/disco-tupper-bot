import discord
from loguru import logger


async def get_webhook(
    bot: discord.Client, channel_id: int
) -> tuple[discord.Webhook, discord.Thread]:
    # TODO exception if limit of used webhooks
    try:
        channel = await bot.fetch_channel(channel_id)
        thread = discord.utils.MISSING
        if channel.type == discord.ChannelType.public_thread:
            thread = channel
            channel = channel.parent

        webhooks_list = await channel.webhooks()
        bot_webhook_name = str(bot.user.id)

        webhook = None
        for webhook_to_check in webhooks_list:
            if webhook_to_check.name == bot_webhook_name:
                webhook = webhook_to_check

        if webhook is None:
            webhook = await channel.create_webhook(name=bot_webhook_name)
            logger.info(f"Created new webhook in channel {channel_id}")

        return webhook, thread
    except discord.Forbidden:
        logger.error(
            f"Bot does not have permissions to fetch/create webhooks in channel {channel_id}"
        )
    except discord.NotFound:
        logger.error(f"Channel with ID {channel_id} not found")
    except discord.HTTPException as e:
        logger.error(f"Failed to fetch/create webhooks in channel {channel_id}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in _get_webhook: {e}")
