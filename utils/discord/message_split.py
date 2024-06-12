import re


class TextFormatterSplit:
    """chatGpt shit with this code
    https://github.com/mwittrien/BetterDiscordAddons/blob/f3cdac8d7ea6cefce1e1a37861d0fcf62ca16bdf/Plugins/SplitLargeMessages/SplitLargeMessages.plugin.js#L67
    """

    def __init__(self, max_world_length=1000, max_message_length=1500, base_separator="\n"):
        self.base_separator = base_separator
        self.separator_escaped = self.base_separator.replace('\n', '\\n')

        if max_world_length > max_message_length:
            raise ValueError("split_message_length more then max_length")

        self.max_world_length = int(max_world_length * (19 / 20))
        self.max_message_length = max_message_length

        # Выбрать все предложения которые длинее определенной длины
        self.long_words_regex = f"[^{self.separator_escaped} ]{{{self.max_world_length},}}"
        print(self.long_words_regex)

    def format_text(self, text):

        text = text.replace('\t', '    ')

        long_words = re.findall(self.long_words_regex, text, re.MULTILINE)
        # Поиск всех строк которые больше длины self.split_message_length

        if long_words:
            # Если у нас есть слова которые очень длинные!
            for long_word in long_words:
                world_step = 0
                short_words = []
                for character in long_word:
                    character_is_new_line = character == '\n'
                    current_word_is_near_to_limit = len(short_words[world_step]) >= (self.max_world_length - 200)

                    current_word_out_of_limit = len(short_words[world_step]) >= self.max_world_length

                    start_new_word = (current_word_out_of_limit or (
                            character_is_new_line and current_word_is_near_to_limit))

                    if short_words and start_new_word:
                        # Если текущее слово или слишком длинное или примерно около лимита то мы начинаем делать новове слово.
                        world_step += 1

                    if world_step >= len(short_words):
                        # Добавляем новый элемент в список что бы не поесть говна...
                        short_words.append('')

                    short_words[world_step] += character

                # Замена длинных слов на их разделеный аналог...
                text = text.replace(long_word, self.base_separator.join(short_words))

        messages = [""]
        message_count = 0

        # Проходим по всем артикулам по разделителю
        for article in text.split(self.base_separator):

            text_to_count = (messages[message_count] + article).replace(self.base_separator, '').replace(' ', '')

            sentence_more_then = len(text_to_count) > self.max_world_length * (39 / 40)

            if messages and sentence_more_then:
                message_count += 1

            if message_count >= len(messages):
                # Создаем новый сообщение
                messages.append('')

            messages[message_count] += article + self.base_separator

        insert_code_block, insert_code_line = None, None

        for message_i in range(len(messages)):
            if insert_code_block:
                messages[message_i] = insert_code_block + messages[message_i]
                insert_code_block = None
            elif insert_code_line:
                messages[message_i] = insert_code_line + messages[message_i]
                insert_code_line = None

            # Найти блоки кода
            code_blocks = re.findall('```[\\S]*\\n|```', messages[message_i], re.MULTILINE)

            # Найти блоки кода в линию
            code_lines = re.findall('[^`]`{1,2}[^`]|[^`]`{1,2}[^`]{0,1}', messages[message_i], re.MULTILINE)

            if code_blocks and len(code_blocks) % 2 == 1:
                messages[message_i] += "```"
                insert_code_block = code_blocks[-1] + '\n'
            elif code_lines and len(code_lines) % 2 == 1:
                insert_code_line = ''.join(c for c in code_lines[-1] if c == '`')
                messages[message_i] += insert_code_line

        return messages
