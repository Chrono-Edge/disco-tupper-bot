from localization import locale

async def get_template_start(user, text):
    async for tupper in user.tuppers:
        l, r = split_template(tupper.call_pattern)

        if text.startswith(l):
            return tupper, l, r
        
    return None


def validate_template(text):
    text = text.strip()

    if "text" not in text:
        raise SyntaxError(locale.template_should_contain_at_least_one_placeholder)

    if len(text) <= 4:
        raise SyntaxError(
            locale.template_should_contain_something_aside_from_placeholder
        )

    if not split_template(text)[0]:
        raise SyntaxError(
            locale.template_should_contain_something_aside_from_placeholder
        )
    
    return text


def split_template(text):
    text = text.strip()

    return text.split("text", 1)
