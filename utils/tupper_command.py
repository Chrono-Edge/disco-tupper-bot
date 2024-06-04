import shlex
from collections import namedtuple

from utils.dices import roll_dices
from database.models.user import User

Command = namedtuple("Command", ["name", "args", "argc"])


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
    return f"Текущий баланс: {tupper.balance}."

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
        return f"Баланс слишком низкий: текущий баланс: `{tupper.balance}`, нужно: `{amount}`."

    balance = tupper.balance - amount
    await tupper.update(balance=balance)
    await to_tupper.update(balance=to_tupper.balance + amount)

    return f"Успешно. Текущий баланс: `{balance}`."

TUPPER_COMMANDS = {
    "roll": _command_roll,
    "balance": _command_balance,
    "send": _command_send,
}
for key in TUPPER_COMMANDS:
    TUPPER_COMMANDS[key[0]] = TUPPER_COMMANDS[key]

async def handle_tupper_command(ctx, tupper, message_content):
    command = parse_tupper_command(message_content)
    if not command:
        return

    if command.name not in TUPPER_COMMANDS:
        return
    
    await TUPPER_COMMANDS[command.name](ctx, tupper, command)
    