import re
import random
import operator
from localization import locale
from utils.rand import randint


async def _roll(count, sides):
    if count <= 0:
        raise ValueError(locale.number_of_dices_should_be_gtz)

    if sides <= 0:
        raise ValueError(locale.number_of_sides_should_be_gtz)

    rolls = []
    for _ in range(count):
        rolls.append(await randint(1, sides))

    return rolls


OPS = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    "%": operator.mod,
    "^": operator.pow,
}
OPS_KEYS = "".join(OPS.keys()).replace("-", r"\-")

T_NAME = re.compile(r"([abce-zа-ге-йл-яA-ZА-Я]+)")
T_COLON = re.compile(r"(:)")
T_DICE = re.compile(r"(d|д|к)")
T_MINUS = re.compile(r"(-)")
T_OP = re.compile(f"([{OPS_KEYS}])")
T_DIGIT = re.compile(r"(\d+)")
T_OPEN_PAREN = re.compile(r"(\()")
T_CLOSE_PAREN = re.compile(r"(\))")
T_WS = re.compile(r"([ \t\r\n]+)")

TOKEN_NAMES = {
    T_NAME: locale.T_NAME,
    T_COLON: locale.T_COLON,
    T_DICE: locale.T_DICE,
    T_OP: locale.T_OP,
    T_DIGIT: locale.T_DIGIT,
    T_OPEN_PAREN: locale.T_OPEN_PAREN,
    T_CLOSE_PAREN: locale.T_CLOSE_PAREN,
}


class Value:
    def __init__(self, value):
        if not isinstance(value, list):
            value = [int(value)]

        self.value = value

    def __int__(self):
        return sum(map(int, self.value))

    def __repr__(self):
        return str(self.value[0] if len(self.value) == 1 else self.value)

    def __iter__(self):
        return iter(self.value)

    def __next__(self):
        return next(self.value)

    def __index__(self, index):
        return self.value[index]

    def __len__(self):
        return len(self.value)

    def __eq__(self, other):
        if not isinstance(other, Value):
            return False

        return self.value == other.value

    def apply(self, what, *args):
        args = list(map(int, args))

        return Value(what(int(self), *args))


class Dices:
    def __init__(self, text):
        self.text = text.strip()
        self.position = 0

        self.names = {}
        self.rolls = []
        self.result = None

        self._rolls = []

    def __repr__(self):
        if self.result:
            buffer = ""

            for count, sides, roll in self._rolls:
                buffer += f"{'' if count == 1 else count}d{sides}: {roll}\n"

            for roll, result in zip(self.rolls, self.result):
                count, sides, roll = roll

                buffer += f"{'' if count == 1 else count}d{sides}: "

                roll_sum = int(roll)
                result_sum = int(result)
                if result_sum == roll_sum:
                    results = ", ".join(map(str, result))

                    if "," in results:
                        results = f"[{results}]"

                    buffer += results

                    if "," in results:
                        buffer += f" ({result_sum})"

                    buffer += "\n"
                else:
                    difference = result_sum - roll_sum
                    results = f"{'' if len(roll) == 1 else f'{roll_sum} -> '}{roll_sum}{'' if difference < 0 else '+'}{difference}"

                    buffer += f"{roll} -> {results} ({int(result)})\n"

            return f"```\n{self.text}\n{buffer}= {int(self.result)}```"

        return self.text

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
        raise SyntaxError(
            locale.format(
                "unexpected_input", position=self.position + 1, expected=expected
            )
        )

    def _expect(self, what):
        match = self._match(what)
        if not match:
            self._expected(TOKEN_NAMES[what])

        return match

    async def _parse_dice(self, left=1):
        if self._match(T_OPEN_PAREN):
            right = await self._parse_expr()

            self._expect(T_CLOSE_PAREN)
        else:
            right = await self._parse_atom()

        left = int(left)
        right = int(right)

        if left > 1000 or right > 1000:
            raise SyntaxError(locale.too_long_number)

        roll = Value(await _roll(left, right))

        self._rolls.append((left, right, roll))

        return roll

    async def _parse_atom(self):
        if self._match(T_OPEN_PAREN):
            expr = await self._parse_expr()

            self._expect(T_CLOSE_PAREN)

            if self._match(T_DICE, skip_ws=False):
                return await self._parse_dice(expr)

            return expr
        elif self._match(T_MINUS):
            value = await self._parse_atom()

            return value.apply(operator.neg)
        elif match := self._match(T_DIGIT):
            try:
                left = int(match[0])
            except ValueError:
                raise SyntaxError(locale.too_long_number)

            if match := self._match(T_DICE, skip_ws=False):
                return await self._parse_dice(left)

            return Value(left)
        elif self._match(T_DICE):
            return await self._parse_dice()
        elif match := self._match(T_NAME):
            name = match[0].upper()

            if name not in self.names:
                raise NameError(
                    locale.format("undefined_variable", variable_name=match[0])
                )

            expr = self.names[name]

            if self._match(T_DICE, skip_ws=False):
                return await self._parse_dice(expr)

            return expr

        self._expected(locale.number_dice_or_a_variable)

    async def _parse_expr(self):
        left = await self._parse_atom()

        if op := self._match(T_OP):
            op = OPS[op[0]]
            right = await self._parse_expr()

            left = left.apply(op, right)
        elif self._match(T_COLON):
            right = self._expect(T_NAME)[0].upper()

            self.names[right] = left

        return left

    async def _parse_exprs(self):
        exprs = []
        while not self._done():
            if len(exprs) >= 10:
                raise SyntaxError(locale.too_long_number)

            rolls_count = len(self._rolls)

            expr = await self._parse_expr()

            if len(self._rolls) == rolls_count:
                raise SyntaxError(locale.expression_does_not_contain_rolls)

            self.rolls.append(self._rolls.pop(-1))

            exprs.append(expr)

        if not exprs:
            raise SyntaxError(locale.expression_should_not_be_empty)

        return Value(exprs)

    async def roll(self, vars={}):
        self.names = {str(k).upper(): Value(vars[k]) for k in vars}
        self.position = 0
        self.rolls = []
        self._rolls = []

        self.result = await self._parse_exprs()

        return self


async def roll_dices(dices, vars={}):
    dices = Dices(dices)

    try:
        await dices.roll(vars=vars)
    except (ValueError, SyntaxError, NameError) as e:
        return str(e)
    except ZeroDivisionError:
        return locale.division_by_zero

    return str(dices)
