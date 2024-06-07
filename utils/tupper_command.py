import re
import shlex
from collections import namedtuple

import discord
from loguru import logger

import config

from utils.dices import roll_dices
from database.models.attribute import Attribute
from database.models.tupper import Tupper
from database.models.item import Item
from utils.encoding.non_printable import NonPrintableEncoder
from utils.encoding.non_printable import HEADER

from localization import locale
from tortoise.expressions import F

Command = namedtuple("Command", ["name", "args", "argc"])


async def get_webhook(
        bot: discord.Client, channel_id: int
) -> (discord.Webhook, discord.Thread):
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


async def get_tupper_id(call_message):
    if not call_message.reference:
        return None

    channel = await bot.fetch_channel(call_message.reference.channel_id)
    if not channel:
        return None

    message = await channel.fetch_message(call_message.reference.message_id)
    if not message:
        return None

    if message.content.find(HEADER) <= -1:
        return None

    _, metadata_dict = NonPrintableEncoder.decode_dict(message.content)

    if "tupper_id" not in metadata_dict:
        return None

    return int(metadata_dict["tupper_id"])


def parse_tupper_command(text):
    text = text.strip()

    if not text or not text.startswith(tuple(config.prefixes)):
        return None

    try:
        parts = shlex.split(text[1:])
    except Exception as e:
        return None

    if len(parts) < 1:
        return None

    return Command(name=parts[0].lower(), args=parts[1:], argc=len(parts) - 1)


async def _command_roll(call_message, tupper, command):
    """Dice roll"""
    if command.argc < 1:
        return

    vars = {}
    async for attr in tupper.attrs:
        vars[attr.name] = attr.value

    return roll_dices(" ".join(command.args), vars=vars)


async def _command_balance(call_message, tupper, command):
    return locale.format("current_balance", balance=tupper.balance)


async def _command_send(call_message, tupper, command):
    """Send money to another tupper"""
    if command.argc != 1:
        return None

    tupper_id = await get_tupper_id(call_message)
    if tupper_id is None:
        return locale.reference_message_not_found

    to_tupper = await Tupper.get(id=tupper_id)
    if not to_tupper:
        return locale.no_such_tupper

    try:
        amount = abs(int(command.args[0]))
    except ValueError:
        return None

    try:
        amount = abs(int(amount))
    except ValueError:
        return None

    if amount > tupper.balance:
        return locale.format("balance_is_too_low", need=amount, have=tupper.balance)

    new_balance = tupper.balance - amount
    await Tupper.filter(id=tupper.id).update(balance=new_balance)
    await Tupper.filter(id=to_tupper).update(balance=F("balance") + amount)

    return locale.format("current_balance", balance=new_balance)


async def _command_attributes(call_message, tupper, command):
    """command attributes set"""
    # TODO info text from localization
    if command.argc == 2:
        name = command.args[0].strip().lower()
        if not re.match(r"^[а-яa-z]{2,3}$", name):
            return locale.illegal_attribute_name

        try:
            value = int(command.args[1])
        except ValueError:
            return None

        if not await tupper.attrs.filter(name=name).exists():
            await Attribute.create(owner=tupper, name=name, value=value)
        else:
            await tupper.attrs.filter(name=name).update(value=value)

        return locale.attribute_was_successfully_changed

    buffer = ""

    async for attr in tupper.attrs:
        buffer += f"`{attr.name}`: `{attr.value}`\n"

    if len(tupper.attrs) == 0:
        buffer += locale.empty

    return buffer


async def _command_inventory(call_message, tupper, command):
    """inventory commands"""
    # TODO info text from localization
    buffer = f"Inventory of `{tupper.name}`:"

    async for item in tupper.items:
        buffer += f"`{item.name}` ({item.quantity})\n"

    if len(tupper.items) == 0:
        buffer += locale.empty

    return buffer


async def _command_take(call_message, tupper, command):
    """Take item"""
    if command.argc not in (1, 2):
        return None

    if command.argc >= 1:
        name = command.args[0].strip().lower()

    if command.argc == 2:
        try:
            quantity = abs(int(command.args[1]))
        except ValueError:
            return None
    else:
        quantity = 1

    item = await Item.filter(name=name, tupper_owner=tupper).first()
    if not item:
        await Item.create(name=name, quantity=quantity, tupper_owner=tupper)
    else:
        await Item.filter(id=item.id).update(quantity=F("quantity") + quantity)

    return locale.format("successfully_obtained", name=name, quantity=quantity)


async def _command_give(call_message, tupper, command):
    """give out item"""
    if command.argc not in (1, 2):
        return None

    tupper_id = await get_tupper_id(call_message)
    if tupper_id is None:
        return locale.reference_message_not_found

    to_tupper = await Tupper.get(id=tupper_id)
    if not to_tupper:
        return locale.no_such_tupper

    if command.argc == 1:
        name = command.args[0].strip().lower()
        quantity = 1
    elif command.argc == 2:
        name = command.args[0].strip().lower()
        try:
            quantity = abs(int(command.args[1]))
        except ValueError:
            return None

    item = await Item.filter(name=name, tupper_owner=tupper).first()
    if not item:
        return locale.not_enough_items

    if item.quantity < quantity:
        return locale.not_enough_items

    if quantity == item.quantity:
        await Item.filter(id=item.id).delete()
    else:
        await Item.filter(id=item.id).update(quantity=F("quantity") - quantity)

    item = await Item.filter(name=name, tupper_owner=to_tupper).first()
    if not item:
        await Item.create(name=name, quantity=quantity, tupper_owner=to_tupper)
    else:
        await Item.filter(id=item.id).update(quantity=F("quantity") + quantity)

    return locale.format("successfully_gived", name=name, quantity=quantity)


TUPPER_COMMANDS = {
    "roll": _command_roll,
    "balance": _command_balance,
    "send": _command_send,
    "attributes": _command_attributes,
    "inventory": _command_inventory,
    "take": _command_take,
    "give": _command_give,
}

for key in dict(TUPPER_COMMANDS):
    TUPPER_COMMANDS[key[0]] = TUPPER_COMMANDS[key]


async def handle_tupper_command(message: discord.Message, tupper, message_content):
    command = parse_tupper_command(message_content)
    if not command:
        return

    if command.name not in TUPPER_COMMANDS:
        return

    return await TUPPER_COMMANDS[command.name](message, tupper, command)
