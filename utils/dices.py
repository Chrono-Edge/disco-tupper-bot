import re
import random
import operator

OPS = {
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '/': operator.truediv,
    '%': operator.mod,
    '^': operator.pow,
}

T_NAME = re.compile(r'([a-zA-Zа-яА-Я_][a-zA-Zа-яА-Я0-9_]*)')
T_COLON = re.compile(r'(:)')
T_DICE = re.compile(r'(d)')
T_MINUS = re.compile(r'(-)')
T_TILDA = re.compile(r'(~)')
T_EXCL = re.compile(r'(!)')
T_OP = re.compile(f'([{''.join(OPS.keys()).replace('-', r'\-')}])')
T_DIGIT = re.compile(r'(\d+)')
T_OPEN_PAREN = re.compile(r'(\()')
T_CLOSE_PAREN = re.compile(r'(\))')
T_WS = re.compile(r'([ \t\r\n]+)')

TOKEN_NAMES = {
    T_NAME: 'имя',
    T_COLON: 'двоеточие',
    T_TILDA: 'тильда',
    T_EXCL: 'восклицательный знак',
    T_DICE: 'кость',
    T_OP: 'оператор',
    T_DIGIT: 'число',
    T_OPEN_PAREN: 'открывающая скобка',
    T_CLOSE_PAREN: 'закрывающая скобка'
}


class Value:
    def __init__(self, value):
        if type(value) is not list:
            value = [int(value)]

        self.value = value

    def __int__(self):
        return sum(map(int, self.value))

    def __repr__(self):
        return str(self.value[0] if len(self.value) == 1 else self.value)

    def apply(self, what, *args):
        args = list(map(int, args))

        return Value(list(map(lambda n: what(int(n), *args), self.value)))


class Dices:
    def __init__(self, text):
        self.text = text.strip().lower()
        self.position = 0

        self.names = {}
        self.rolls = []
        self.has_rolls = False
        self.result = None

    def __repr__(self):
        if self.result:
            return f'`{self.text}`: `{self.rolls}`; `{self.result}` (`{int(self.result)}`)'

        return self.text

    def _roll(self, count, sides, dont_save=False):
        if count <= 0:
            raise ValueError('Количество костей должно быть больше нуля.')

        if sides <= 0:
            raise ValueError('Количество сторон должно быть больше нуля.')

        rolls = []
        for _ in range(count):
            rolls.append(random.randint(1, sides))

        if not dont_save:
            self.rolls.append(Value(rolls))

        if not self.has_rolls:
            self.has_rolls = True

        return rolls

    def _skip_ws(self):
        match = T_WS.match(self.text, self.position)
        if match:
            self.position += len(match.group(0))

    def _done(self):
        self._skip_ws()

        return self.position >= len(self.text)

    def _match(self, what, skip_ws=True):
        if skip_ws:
            self._skip_ws()

        match = what.match(self.text, self.position)
        if match:
            self.position += len(match.group(0))

            return match.groups()

    def _expected(self, expected):
        raise SyntaxError(f'Неожиданный ввод на позиции # {self.position + 1}: ожидалось: {expected}.')

    def _expect(self, what):
        match = self._match(what)
        if not match:
            self._expected(TOKEN_NAMES[what])

        return match

    def _parse_dice(self, left=1):
        if self._match(T_OPEN_PAREN):
            right = self._parse_expr()

            self._expect(T_CLOSE_PAREN)
        else:
            right = self._parse_atom()

        dont_save = self._match(T_EXCL)

        left = int(left)
        right = int(right)

        return Value(self._roll(left, right, dont_save=dont_save))

    def _parse_atom(self):
        if self._match(T_OPEN_PAREN):
            expr = self._parse_expr()

            self._expect(T_CLOSE_PAREN)

            if self._match(T_DICE):
                return self._parse_dice(expr)

            return expr
        elif self._match(T_MINUS):
            return self._parse_atom().apply(operator.neg)
        elif self._match(T_TILDA):
            return Value(int(self._parse_atom()))
        elif match := self._match(T_DIGIT):
            left = int(match[0])

            if match := self._match(T_DICE, skip_ws=False):
                return self._parse_dice(left)

            return Value(left)
        elif self._match(T_DICE):
            return self._parse_dice()
        elif match := self._match(T_NAME):
            name = match[0]

            if name not in self.names:
                raise NameError(f'Неизвестная переменная: `{name}`.')

            return self.names[name]

        self._expected('число, кость или открывающая скобка')

    def _parse_expr(self):
        left = self._parse_atom()

        if op := self._match(T_OP):
            op = OPS[op[0]]
            right = self._parse_expr()

            left = left.apply(op, right)
        elif self._match(T_COLON):
            right = self._expect(T_NAME)[0]

            self.names[right] = left

            return

        return left

    def _parse_exprs(self):
        exprs = []
        while not self._done():
            expr = self._parse_expr()

            if expr is not None:
                exprs.append(expr)

        if not exprs:
            raise SyntaxError('Выражение не должно быть пустым.')

        return Value(exprs)

    def roll(self, vars={}):
        self.names = {str(k).lower(): Value(vars[k]) for k in vars}
        self.position = 0
        self.rolls = []
        self.has_rolls = False

        self.result = self._parse_exprs()

        if not self.has_rolls:
            raise ValueError('Выражение не содержит бросков.')

        return self


if __name__ == '__main__':
    print(Dices('d20').roll())
    print(Dices('2d20').roll())
    print(Dices('2d20+3').roll())
    print(Dices('2d20 + 2d20').roll())
    print(Dices('d20 d20+3').roll())
    print(Dices('5d20').roll())
    print(Dices('d20 + (d5 * 5)').roll())
    print(Dices('-d5').roll())
    print(Dices('-d5 + -d5').roll())
    print(Dices('d20+5 d20+3').roll())
    print(Dices('(5d20) * 2 d20').roll())
    print(Dices('d(5*2)').roll())
    print(Dices('d20:x x*2').roll())
    print(Dices('2d5:x x+1').roll())
    print(Dices('2d5:x ~(x+1)').roll())
    print(Dices('2d5!:x dx').roll())
    print(Dices('4d4:x x*2').roll())
    print(Dices('4d4:x ~x*2').roll())
    print(Dices('d20+ЛВК').roll({'ЛВК': 5}))
