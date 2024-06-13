from localization import locale


async def get_template_start(user, text):
    text = text.lstrip()

    async for tupper in user.tuppers:
        l, r = split_template(tupper.call_pattern)

        if text.startswith(l):
            return tupper, l, r

    return None


def split_template(text):
    text = text.strip()

    l, r = text.split("text", 1)

    return l.lstrip(), r.strip()


def validate_template(text):
    text = text.lower().strip()

    if "text" not in text:
        text += "text"

    parts = split_template(text)
    if len(parts) != 2 or not parts[0]:
        raise SyntaxError(
            locale.template_should_contain_something_aside_from_placeholder
        )

    return text
