from localization import locale


def parse_template(text):
    text = text.strip()

    buffer = ""
    escape = False
    has_star = False
    group = 0
    group_size = 0
    for ch in text:
        if not escape:
            if ch == "*" and not group:
                if has_star:
                    raise SyntaxError(
                        locale.template_should_not_contain_more_than_one_placeholder
                    )

                has_star = True

                buffer += "(.*)"

                continue
            elif ch == "?" and not group:
                buffer += "."

                continue
            elif ch == "[" and not group:
                group = True

                buffer += "["

                continue
            elif ch == "\\":
                escape = True

                continue

        if group and not escape:
            if ch == "]":
                if group_size == 0:
                    raise SyntaxError(locale.empty_blocks_are_forbidden)

                group = False
                group_size = 0

                buffer += "]"

                continue

            group_size += 1

        escape = False

        if ch in r"\.+*?[-]():":
            buffer += "\\"

        buffer += ch

    if group:
        raise SyntaxError(locale.missing_closing_bracket)

    if escape:
        raise SyntaxError(locale.incorrect_escape)

    if not has_star:
        raise SyntaxError(locale.template_should_contain_at_least_one_placeholder)

    if len(buffer) <= 4:
        raise SyntaxError(
            locale.template_should_contain_something_aside_from_placeholder
        )

    return f"^{buffer}$"


def unparse_template(text):
    text = text[1:-1]

    buffer = ""
    escape = False
    in_block = False
    i = 0
    while i < len(text):
        ch = text[i]
        if in_block:
            buffer += ch

            i += 1

            continue

        if escape:
            buffer += ch

            escape = False

            i += 1

            continue

        if ch == ".":
            buffer += "?"
        elif ch == "\\":
            escape = True
        elif ch == "[":
            buffer += ch

            in_block = True
        elif ch == "]":
            buffer += ch

            in_block = False
        elif text[i : i + 4] == "(.*)":
            buffer += "*"

            i += 3
        else:
            buffer += ch

        i += 1

    return buffer


if __name__ == "__main__":
    print(parse_template(r"99 *"))
    print(parse_template(r"k:*"))
    print(parse_template(r"(*)"))
    print(parse_template(r"aaa*bbbb"))
    print(parse_template(r"\*\**\*\*"))
    print(parse_template(r".*."))
    print(parse_template(r"\\a*b\\"))
    print(parse_template(r"[ae]*[ea]"))
    print(parse_template(r"/?/ * /?/"))
    print(parse_template(r"[*]*"))
    print(parse_template(r"[[\]]*"))
    print(parse_template(r"[??]?*"))
    print(parse_template(r"* z"))
