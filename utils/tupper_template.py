from collections import namedtuple
from enum import Enum

from localization import locale

PseudoTupper = namedtuple("Tupper", "id")

class PatternType(Enum):
    NONE = 0
    LEFT_AND_RIGHT = 1
    LEFT_ONLY = 2
    RIGHT_ONLY = 3


class TupperCallPattern:
    def __init__(self, tupper):
        if tupper is None:
            self.tupper = PseudoTupper(-1)
            self.pattern = ""
            self.charlist = set()
            self.left_pattern_part = ""
            self.right_pattern_part = ""
            self.pattern_type = PatternType.NONE
        else:
            self.tupper = tupper
            self.pattern = tupper.template
            self.charlist = set(self.pattern.replace("text", "", 1))

            self.left_pattern_part = tupper.template_l
            self.right_pattern_part = tupper.template_r

            if self.left_pattern_part and self.right_pattern_part:
                self.pattern_type = PatternType.LEFT_AND_RIGHT
            elif self.left_pattern_part and not self.right_pattern_part:
                self.pattern_type = PatternType.LEFT_ONLY
            elif not self.left_pattern_part and self.right_pattern_part:
                self.pattern_type = PatternType.RIGHT_ONLY

    def __hash__(self):
        return f"{self.pattern}-{self.tupper.id}"

    def __repr__(self):
        return f"TupperCallPattern({self.pattern}, {self.tupper.id}, [{self.left_pattern_part}|{self.right_pattern_part}])"

    def is_only_left(self) -> bool:
        return self.pattern_type == PatternType.LEFT_ONLY

    def is_only_right(self) -> bool:
        return self.pattern_type == PatternType.RIGHT_ONLY

    def is_left_and_right(self) -> bool:
        return self.pattern_type == PatternType.LEFT_AND_RIGHT

    def is_none(self) -> bool:
        return self.pattern_type == PatternType.NONE

    def text_startswith(self, text: str) -> bool:
        return text.startswith(self.left_pattern_part) and (
            self.left_pattern_part != ""
        )

    def text_endswith(self, text: str) -> bool:
        return text.endswith(self.right_pattern_part) and (
            self.right_pattern_part != ""
        )

    def format_text(self, text):
        if self.text_startswith(text):
            text = text[len(self.left_pattern_part) :].lstrip()
        if self.text_endswith(text):
            text = text[: len(text) - len(self.right_pattern_part)].rstrip()
        return text


def split_template(text):
    text = text.lower().strip()

    if "text" not in text:
        text += "text"

    l, r = text.split("text", 1)
    l, r = l.lstrip(), r.strip()

    if not l and not r:
        raise SyntaxError(
            locale.template_should_contain_something_aside_from_placeholder
        )

    return text, l, r
