import re
import random
import operator


from localization import locale

OPS = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    "%": operator.mod,
    "^": operator.pow,
}
OPS_KEYS = "".join(OPS.keys()).replace("-", r"\-")

T_NAME = re.compile(r"([abce-zа-яABCE-ZА-Я]+)")
T_COLON = re.compile(r"(:)")
T_DICE = re.compile(r"(d)")
T_MINUS = re.compile(r"(-)")
T_TILDE = re.compile(r"(~)")
T_EXCL = re.compile(r"(!)")
T_OP = re.compile(f"([{OPS_KEYS}])")
T_DIGIT = re.compile(r"(\d+)")
T_OPEN_PAREN = re.compile(r"(\()")
T_CLOSE_PAREN = re.compile(r"(\))")
T_WS = re.compile(r"([ \t\r\n]+)")

TOKEN_NAMES = {
    T_NAME: locale.T_NAME,
    T_COLON: locale.T_COLON,
    T_TILDE: locale.T_TILDE,
    T_EXCL: locale.T_EXCL,
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

    def apply(self, what, *args):
        args = list(map(int, args))

        return Value(list(map(lambda n: what(int(n), *args), self.value)))


class Dices:
    def __init__(self, text):
        self.text = text.strip()
        self.position = 0

        self.names = {}
        self.rolls = []
        self.has_rolls = False
        self.result = None

    def __repr__(self):
        if self.result:
            buffer = ""

            for roll, result in zip(self.rolls, self.result):
                count, sides, roll = roll

                results = ", ".join(
                    map(
                        lambda t: f"{t[0]}+{t[1]}" if t[1] != 0 else str(t[0]),
                        zip(roll, map(lambda t: t[1] - t[0], zip(roll, result))),
                    )
                )

                if "," in results:
                    results = f"[{results}]"

                buffer += f"{'' if count == 1 else count}d{sides}: {roll} -> {results} ({int(result)})\n"

            return f"```{self.text}\n{buffer}= {int(self.result)}```"

        return self.text

    def _roll(self, count, sides, dont_save=False):
        if count <= 0:
            raise ValueError(locale.number_of_dices_should_be_gte)

        if sides <= 0:
            raise ValueError(locale.number_of_sides_should_be_gte)

        rolls = []
        for _ in range(count):
            rolls.append(random.randint(1, sides))

        if not dont_save:
            self.rolls.append((count, sides, Value(rolls)))

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

    def _parse_dice(self, left=1):
        if self._match(T_OPEN_PAREN):
            right = self._parse_expr()

            self._expect(T_CLOSE_PAREN)
        else:
            right = self._parse_atom()

        dont_save = self._match(T_EXCL)

        left = int(left)
        right = int(right)

        return Value(self._roll(left, right, dont_save=bool(dont_save)))

    def _parse_atom(self):
        if self._match(T_OPEN_PAREN):
            expr = self._parse_expr()

            self._expect(T_CLOSE_PAREN)

            if self._match(T_DICE, skip_ws=False):
                return self._parse_dice(expr)

            return expr
        elif self._match(T_MINUS):
            return self._parse_atom().apply(operator.neg)
        elif self._match(T_TILDE):
            return Value(int(self._parse_atom()))
        elif match := self._match(T_DIGIT):
            left = int(match[0])

            if match := self._match(T_DICE, skip_ws=False):
                return self._parse_dice(left)

            return Value(left)
        elif self._match(T_DICE):
            return self._parse_dice()
        elif match := self._match(T_NAME):
            name = match[0].lower()

            if name not in self.names:
                raise NameError(locale.format("undefined_variable", name=match[0]))

            expr = self.names[name]

            if self._match(T_DICE, skip_ws=False):
                return self._parse_dice(expr)

            return expr

        self._expected(locale.number_dice_or_a_variable)

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
            raise SyntaxError(locale.expression_should_not_be_empty)

        return Value(exprs)

    def roll(self, vars={}):
        self.names = {str(k).lower(): Value(vars[k]) for k in vars}
        self.position = 0
        self.rolls = []
        self.has_rolls = False

        self.result = self._parse_exprs()

        if not self.has_rolls:
            raise ValueError(locale.expression_does_not_contain_rolls)

        return self


def roll_dices(dices, vars={}):
    dices = Dices(dices)

    try:
        dices.roll(vars=vars)
    except (ValueError, SyntaxError, NameError) as e:
        return str(e)
    except ZeroDivisionError:
        return locale.division_by_zero

    return str(dices)


if __name__ == "__main__":
    print(Dices("d20").roll())
    print(Dices("1d20").roll())
    print(Dices("2d20").roll())
    print(Dices("2d20+3").roll())
    print(Dices("2d20 + 2d20").roll())
    print(Dices("d20 d20+3").roll())
    print(Dices("5d20").roll())
    print(Dices("d20 + (d5 * 5)").roll())
    print(Dices("-d5").roll())
    print(Dices("-d5 + -d5").roll())
    print(Dices("d20+5 d20+3").roll())
    print(Dices("(5d20) * 2 d20").roll())
    print(Dices("d(5*2)").roll())
    print(Dices("d20:x x*2").roll())
    print(Dices("2d5:x x+1").roll())
    print(Dices("2d5:x ~(x+1)").roll())
    print(Dices("2d5!:x dx").roll())
    print(Dices("4d4:x x*2").roll())
    print(Dices("4d4:x ~x*2").roll())
    print(Dices("d20+ЛВК").roll({"ЛВК": 5}))
    print(Dices("ЛВКd5").roll({"ЛВК": 5}))
    print(Dices("ЛВК d5").roll({"ЛВК": 5}))
    print(Dices("d(d5 * d(3d20^5))").roll())
