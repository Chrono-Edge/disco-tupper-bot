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


async def handle_tupper_command(webhook, tupper, message_content):
    command = parse_tupper_command(message_content)
    if not command:
        return

    match command.name:
        case "r" | "roll":
            if command.argc < 1:
                return

            vars = {}
            async for attr in tupper.attrs:
                vars[attr.name] = attr.value

            message_content = roll_dices(" ".join(command.args), vars=vars)

        case "b" | "balance":
            return f"Текущий баланс: {tupper.balance}."

        case "s" | "send":
            if command.argc not in (2, 3):
                return

            member = webhook.guild.get_member_named(command.args[0])
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
