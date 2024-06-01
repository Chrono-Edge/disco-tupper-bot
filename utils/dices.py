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

T_DICE = re.compile(r'd(\d+)')
T_MINUS = re.compile(r'(-)')
T_OP = re.compile(f'([{''.join(OPS.keys()).replace('-', r'\-')}])')
T_DIGIT = re.compile(r'(\d+)')
T_OPEN_PAREN = re.compile(r'(\()')
T_CLOSE_PAREN = re.compile(r'(\))')
T_WS = re.compile(r'([ \t\r\n]+)')

TOKEN_NAMES = {
    T_DICE: 'кость',
    T_OP: 'оператор',
    T_DIGIT: 'число',
    T_OPEN_PAREN: 'открывающая скобка',
    T_CLOSE_PAREN: 'закрывающая скобка'
}


class Value:
    def __init__(self, value):
        if type(value) is not list:
            value = [value]

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

        self.rolls = []
        self.result = None

    def __repr__(self):
        if self.result:
            return f'`{self.text}`: `{self.rolls}`; `{self.result}` (`{int(self.result)}`)'

        return self.text

    def _roll(self, count, sides):
        if count <= 0:
            raise ValueError('Количество костей должно быть больше нуля.')

        if sides <= 0:
            raise ValueError('Количество сторон должно быть больше нуля.')

        rolls = []
        for _ in range(count):
            rolls.append(random.randint(1, sides))

        self.rolls.append(Value(rolls))

        return rolls

    def _done(self):
        return self.position >= len(self.text)

    def _skip_ws(self):
        match = T_WS.match(self.text, self.position)
        if match:
            self.position += len(match.group(0))

    def _match(self, what, skip_ws=True):
        if skip_ws:
            self._skip_ws()

        match = what.match(self.text, self.position)
        if match:
            self.position += len(match.group(0))

            return match.groups()

    def _expected(self, expected):
        raise SyntaxError(f'Неожиданный ввод на позиции #{
            self.position + 1}: ожидалось: {expected}.')

    def _expect(self, what):
        match = self._match(what)
        if not match:
            self._expected(TOKEN_NAMES[what])

        return match

    def _parse_atom(self):
        if self._match(T_OPEN_PAREN):
            expr = self._parse_expr()

            self._expect(T_CLOSE_PAREN)

            return expr
        elif self._match(T_MINUS):
            return self._parse_atom().apply(operator.neg)
        elif match := self._match(T_DIGIT):
            left = int(match[0])

            if match := self._match(T_DICE, skip_ws=False):
                left = Value(self._roll(left, int(match[0])))

            return Value(left)
        elif match := self._match(T_DICE):
            return Value(self._roll(1, int(match[0])))

        self._expected('число, кость или открывающая скобка')

    def _parse_expr(self):
        left = self._parse_atom()

        if op := self._match(T_OP):
            op = OPS[op[0]]
            right = self._parse_expr()

            left = left.apply(op, right)

        return left

    def _parse_exprs(self):
        exprs = []
        while not self._done():
            exprs.append(self._parse_expr())

        return Value(exprs)

    def roll(self):
        self.position = 0
        self.rolls = []

        self.result = self._parse_exprs()

        if not self.rolls:
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
