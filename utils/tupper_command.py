import shlex
from collections import namedtuple

import discord
from loguru import logger

from utils.dices import roll_dices
from database.models.user import User
from localization import locale

Command = namedtuple("Command", ["name", "args", "argc"])


async def get_webhook(bot, channel_id: int):
    """Get our webhook"""
    # TODO exception if limit of used webhooks
    try:
        channel = await bot.fetch_channel(channel_id)
        webhooks_list = await channel.webhooks()
        bot_webhook_name = str(bot.user.id)

        webhook = None
        for webhook_to_check in webhooks_list:
            if webhook_to_check.name == bot_webhook_name:
                webhook = webhook_to_check

        if webhook is None:
            webhook = await channel.create_webhook(name=bot_webhook_name)
            logger.info(f"Created new webhook in channel {channel_id}")

        return webhook
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


def parse_tupper_command(text):
    text = text.strip()

    if not text or not text.startwith("!"):
        return None

    parts = shlex.split(text[1:])

    if len(parts) < 1:
        return None

    return Command(name=parts[0].lower(), args=parts[1:], argc=len(parts) - 1)


async def _command_roll(ctx, tupper, command):
    if command.argc < 1:
        return

    vars = {}
    async for attr in tupper.attrs:
        vars[attr.name] = attr.value

    return roll_dices(" ".join(command.args), vars=vars)


async def _command_balance(ctx, tupper, command):
    return locale.format("current_balance", balance=tupper.balance)


async def _command_send(ctx, tupper, command):
    if command.argc not in (2, 3):
        return

    member = ctx.guild.get_member_named(command.args[0])
    if not member:
        return

    user = await User.get(discord_id=member.id)
    if not user:
        return

    if command.argc == 2:
        to_tupper = await user.tuppers.first()
        amount = command.args[1]
    else:
        to_tupper = await user.tuppers.filter(name=command.args[1]).first()
        amount = command.args[2]

    if not to_tupper:
        return

    try:
        amount = abs(int(amount))
    except ValueError:
        return

    if amount > tupper.balance:
        return locale.format("balance_is_too_low", need=amount, have=tupper.balance)

    balance = tupper.balance - amount
    await tupper.update(balance=balance)
    await to_tupper.update(balance=to_tupper.balance + amount)

    return locale.format("current_balance", balance=balance)


TUPPER_COMMANDS = {
    "roll": _command_roll,
    "balance": _command_balance,
    "send": _command_send,
}

ALIES_TUPPER_COMMANDS = {}
for key in TUPPER_COMMANDS.keys():
    ALIES_TUPPER_COMMANDS[key[0]] = TUPPER_COMMANDS[key]

TUPPER_COMMANDS.update(ALIES_TUPPER_COMMANDS)

async def handle_tupper_command(ctx, tupper, message_content):
    command = parse_tupper_command(message_content)
    if not command:
        return

    if command.name not in TUPPER_COMMANDS:
        return

    await TUPPER_COMMANDS[command.name](ctx, tupper, command)
