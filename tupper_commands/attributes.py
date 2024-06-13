import re
import operator

from localization import locale
from database.models.attribute import Attribute

HELP = (locale.attributes_params, locale.attributes_desc)

OPS = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": lambda a, b: 0 if b == 0 else int(a / b),
}


def format_attr(attr):
    if attr.limit != 0:
        return f"`{attr.name}`: `{attr.value}`/`{attr.limit}`"
    else:
        return f"`{attr.name}`: `{attr.value}`"


async def handle(ctx):
    buffer = ""

    if ctx.command.argc > 0:
        for arg in ctx.command.args:
            arg = arg.strip().upper()
            if not (
                match := re.match(
                    r"^([А-ЯA-Z]{2,3})(?:(=|\+|-|\*|/)(\d+|X|-)(?:/(\d+|X|-))?)?$", arg
                )
            ):
                return locale.illegal_attribute_name

            name, op, value, limit = match.groups()
            attr = await ctx.tupper.attrs.filter(name=name).first()
            if not value:
                if not attr:
                    return locale.format("no_such_attribute", attribute_name=name)

                buffer += format_attr(attr)
            else:
                if op == "=" and value in "X-":
                    if not attr:
                        return locale.format("no_such_attribute", attribute_name=name)

                    await ctx.tupper.attrs.filter(id=attr.id).delete()

                    await ctx.log(
                        "log_attr_remove",
                        log_attr_name=name,
                        log_jump_url=ctx.message.reference.jump_url
                        if ctx.message.reference
                        else ctx.message.jump_url,
                    )

                    buffer += locale.format(
                        "attribute_was_successfully_removed", attribute_name=name
                    )
                else:
                    try:
                        if value in "X-":
                            value = 0
                        else:
                            value = int(value)
                    except ValueError:
                        return locale.too_long_number

                    if op != "=":
                        if not attr:
                            return locale.format(
                                "no_such_attribute", attribute_name=name
                            )

                        value = OPS[op](attr.value, value)

                    if limit is not None:
                        try:
                            if limit in "X-":
                                limit = 0
                            else:
                                limit = int(limit)
                        except ValueError:
                            return locale.too_long_number

                        old_limit = 0
                        if not attr:
                            attr = await Attribute.create(
                                owner=ctx.tupper, name=name, value=0, limit=limit
                            )
                        else:
                            old_limit = attr.limit
                            attr.limit = limit
                            await attr.save()

                        await ctx.log(
                            "log_attr_set_limit",
                            log_attr_name=name,
                            log_attr_old_value="X" if old_limit == 0 else old_limit,
                            log_attr_new_value="X" if limit == 0 else limit,
                            log_jump_url=ctx.message.reference.jump_url
                            if ctx.message.reference
                            else ctx.message.jump_url,
                        )

                        if limit == 0:
                            buffer += locale.format("limit_disabled", attribute_name=name) + "\n"

                        buffer += locale.format(
                            "successfully_set_limit",
                            attribute_name=name,
                            limit=limit,
                            old_limit="X" if old_limit == 0 else old_limit,
                        ) + "\n"

                    if attr and attr.limit != 0:
                        value = min(value, attr.limit)

                    if attr and value == attr.value:
                        buffer += locale.format(
                            "attribute_was_not_changed", attribute_name=name
                        )
                    else:
                        if not attr:
                            await Attribute.create(
                                owner=ctx.tupper, name=name, value=value
                            )

                            await ctx.log(
                                "log_attr_set",
                                log_attr_name=name,
                                log_attr_new_value=value,
                                log_jump_url=ctx.message.reference.jump_url
                                if ctx.message.reference
                                else ctx.message.jump_url,
                            )
                        else:
                            await ctx.tupper.attrs.filter(id=attr.id).update(
                                value=value
                            )

                            await ctx.log(
                                "log_attr_set",
                                log_attr_name=name,
                                log_attr_old_value=attr.value,
                                log_attr_new_value=value,
                                log_jump_url=ctx.message.reference.jump_url
                                if ctx.message.reference
                                else ctx.message.jump_url,
                            )

                        buffer += locale.format(
                            "attribute_was_successfully_changed",
                            attribute_name=name,
                            value=value,
                            old_value=attr.value if attr else "X",
                        )

            buffer += "\n"
    else:
        async for attr in ctx.tupper.attrs:
            if attr.limit != 0:
                buffer += f"`{attr.name}`: `{attr.value}`/`{attr.limit}`\n"
            else:
                buffer += f"`{attr.name}`: `{attr.value}`\n"

        if len(ctx.tupper.attrs) == 0:
            return locale.empty

    return buffer.rstrip()
