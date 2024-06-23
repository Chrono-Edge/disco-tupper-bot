import copy

from database.models.tupper import Model
from database.models.user import User
from utils.tupper_template import TupperCallPattern, PatternType


class MessageUtilsForTuppers:
    call_patterns_l = []
    call_patterns_r = []
    call_patterns_lr = []
    message_lines = []
    pattern_on_lines = []
    is_tupper_message = False

    # TODO Chain check for class usage
    def __init__(self, db_user: User, message_content: str):
        self.db_user = db_user
        self.message_content = message_content
        self.message_lines = message_content.split("\n")

    async def _gen_possible_call_patterns(self):
        """Return possible patterns in message"""
        call_patterns_l: list[TupperCallPattern] = []
        call_patterns_r: list[TupperCallPattern] = []
        call_patterns_lr: list[TupperCallPattern] = []

        async for tupper in self.db_user.tuppers:
            pattern_to_add = TupperCallPattern(tupper)
            # cut not impossible to use patterns
            if not all(c in self.message_content for c in pattern_to_add.charlist):
                continue

            if pattern_to_add.pattern_type == PatternType.LEFT_ONLY:
                call_patterns_l.append(pattern_to_add)
            elif pattern_to_add.pattern_type == PatternType.RIGHT_ONLY:
                call_patterns_r.append(pattern_to_add)
            elif pattern_to_add.pattern_type == PatternType.LEFT_AND_RIGHT:
                call_patterns_lr.append(pattern_to_add)

        self.call_patterns_l = call_patterns_l
        self.call_patterns_r = call_patterns_r
        self.call_patterns_lr = call_patterns_lr
        return True

    async def is_message_for_tuppers(self) -> bool:
        await self._gen_possible_call_patterns()
        first_pattern_l = None
        first_pattern_r = None
        first_pattern_lr = None

        # Find only left patterns
        for call_pattern in self.call_patterns_l:
            if call_pattern.text_startswith(self.message_content):
                first_pattern_l = True

        # Find only right patterns
        for call_pattern in self.call_patterns_r:
            if call_pattern.text_endswith(self.message_content):
                first_pattern_r = True

        # Find left with right patterns
        for call_pattern in self.call_patterns_lr:
            if call_pattern.text_startswith(self.message_content) or call_pattern.text_endswith(self.message_content):
                first_pattern_lr = True

        # if message not started from template we ignore this message
        if not first_pattern_l and not first_pattern_r and not first_pattern_lr:
            self.is_tupper_message = False
            return False
        self.is_tupper_message = True
        return True

    async def find_all_patterns_on_lines(self):
        patterns_per_line: list[TupperCallPattern] = [TupperCallPattern(None)] * len(self.message_lines)

        for i, line in enumerate(self.message_lines):
            # if left and right in one line this full one actor per line
            for right_left_pattern in self.call_patterns_lr:
                if right_left_pattern.text_startswith(line) and right_left_pattern.text_endswith(line):
                    patterns_per_line[i] = right_left_pattern
                    break

            if not patterns_per_line[i].is_none():
                continue

            # only right text<
            for right_pattern in self.call_patterns_r:
                if right_pattern.text_endswith(line):
                    patterns_per_line[i] = right_pattern
                    break

            if not patterns_per_line[i].is_none():
                continue

            # only left
            for left_pattern in self.call_patterns_l:
                if left_pattern.text_startswith(line):
                    patterns_per_line[i] = left_pattern

            if not patterns_per_line[i].is_none():
                continue

            # right and left set to end. If some strange man set >text and text< and >text< template....

            for right_left_pattern in self.call_patterns_lr:
                if right_left_pattern.text_startswith(line) or right_left_pattern.text_endswith(line):
                    patterns_per_line[i] = right_left_pattern

        self.pattern_on_lines = patterns_per_line

    async def text_fill_left_pattern(self):
        # only left template
        current_left_pattern = None
        for i, pattern in enumerate(self.pattern_on_lines):
            if pattern.is_only_left():
                current_left_pattern = pattern
                continue
            elif not current_left_pattern:
                continue
            elif pattern.is_none():
                copy_pattern = copy.deepcopy(current_left_pattern)
                copy_pattern.pattern_type = PatternType.TEXT
                self.pattern_on_lines[i] = copy_pattern
            else:
                current_left_pattern = None
                continue

    async def text_fill_right_pattern(self):
        # only right template
        for i, pattern in enumerate(self.pattern_on_lines):
            if pattern.is_none() or pattern.is_left_and_right():
                continue

            if pattern.is_only_right():
                # go back for find all strings
                for step_back in range(i - 1, -1, -1):
                    step_back_pattern = self.pattern_on_lines[step_back]

                    if step_back_pattern.is_left_and_right() or step_back_pattern.is_none():
                        copy_pattern = copy.deepcopy(pattern)
                        copy_pattern.pattern_type = PatternType.TEXT
                        self.pattern_on_lines[step_back] = copy_pattern
                    elif step_back_pattern.is_only_right() or step_back_pattern.is_only_left():
                        break

    async def text_fill_right_and_left(self):
        # left and right
        current_left_and_right_pattern: TupperCallPattern = None
        start_index = -1
        for i, pattern in enumerate(self.pattern_on_lines):
            current_text_line = self.message_lines[i]
            if not current_left_and_right_pattern:
                if not pattern.is_left_and_right():
                    continue
                if pattern.text_startswith(current_text_line):
                    if pattern.text_endswith(current_text_line):
                        current_left_and_right_pattern = None
                    else:
                        current_left_and_right_pattern = pattern
                    continue
                else:
                    pattern.pattern_type = PatternType.NONE
            elif pattern.is_left_and_right() and current_left_and_right_pattern:
                if (pattern == current_left_and_right_pattern) \
                        and current_left_and_right_pattern.text_endswith(current_text_line):
                    current_left_and_right_pattern = None
                    continue
                print(pattern, current_left_and_right_pattern)
                pattern_copy = copy.deepcopy(current_left_and_right_pattern)
                pattern_copy.pattern_type = PatternType.TEXT
                self.pattern_on_lines[i] = pattern_copy
                continue
            elif current_left_and_right_pattern and pattern.is_none():
                pattern_copy = copy.deepcopy(current_left_and_right_pattern)
                pattern_copy.pattern_type = PatternType.TEXT

                self.pattern_on_lines[i] = pattern_copy

        return True
