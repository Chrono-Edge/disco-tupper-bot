def parse_template(text):
    text = text.strip()

    buffer = ''
    escape = False
    has_star = False
    group = 0
    group_size = 0
    for ch in text:
        if not escape:
            if ch == '*' and not group:
                if has_star:
                    raise SyntaxError('Шаблон не должен содержать более одной звёздочки (`*`).')
                
                has_star = True

                buffer += '(.*)'

                continue
            elif ch == '?' and not group:
                buffer += '.'

                continue
            elif ch == '[' and not group:
                group = True
                
                buffer += '['

                continue
            elif ch == '\\':
                escape = True

                continue

        if group and not escape:
            if ch == ']':
                if group_size == 0:
                    raise SyntaxError('Пустые []-блоки запрещены.')
                
                group = False
                group_size = 0

                buffer += ']'

                continue

            group_size += 1

        escape = False

        if ch in r'\.+*?[-]():':
            buffer += '\\'

        buffer += ch

    if group:
        raise SyntaxError('Отсутствует закрывающая ]-скобка.')
    
    if escape:
        raise SyntaxError('Некорректное экранирование.')
    
    if not has_star:
        raise SyntaxError('Шаблон должен содержать хотя бу одну звёздочку (`*`).')
    
    if len(buffer) <= 4:
        raise SyntaxError('Шаблон должен содержать что-то помимо звёздочки (`*`).')
    
    return f'^{buffer}$'

if __name__ == '__main__':
    print(parse_template(r'99 *'))
    print(parse_template(r'k:*'))
    print(parse_template(r'(*)'))
    print(parse_template(r'aaa*bbbb'))
    print(parse_template(r'\*\**\*\*'))
    print(parse_template(r'.*.'))
    print(parse_template(r'\\a*b\\'))
    print(parse_template(r'[ae]*[ea]'))
    print(parse_template(r'/?/ * /?/'))
    print(parse_template(r'[*]*'))
    print(parse_template(r'[[\]]*'))
    print(parse_template(r'[??]?*'))
    print(parse_template(r'* z'))
