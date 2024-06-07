import re


class TextFormatterSplit:
    """chatGpt shit with tihs code
    https://github.com/mwittrien/BetterDiscordAddons/blob/f3cdac8d7ea6cefce1e1a37861d0fcf62ca16bdf/Plugins/SplitLargeMessages/SplitLargeMessages.plugin.js#L67
    """
    def __init__(self, settings):
        self.settings = settings

    def format_text(self, text):
        separator = '\n' if self.settings['general']['byNewlines'] else ' '
        split_message_length = self.settings['amounts']['splitCounter']
        if split_message_length < 1000 or split_message_length > self.settings['maxMessageLength']:
            split_message_length = self.settings['amounts']['maxMessageLength']

        text = text.replace('\t', '    ')
        separator_escaped = separator.replace('\n', '\\n')
        long_words_regex = f"[^{separator_escaped}]{{{int(split_message_length * (19 / 20))},}}"
        long_words = re.findall(long_words_regex, text, re.MULTILINE)

        if long_words:
            for long_word in long_words:
                count1 = 0
                short_words = []
                for c in long_word:
                    if (short_words and (len(short_words[count1]) >= split_message_length * (19 / 20) or
                                         (c == '\n' and len(short_words[count1]) >= split_message_length * (
                                                 19 / 20) - 100))):
                        count1 += 1
                    if count1 >= len(short_words):
                        short_words.append('')
                    short_words[count1] += c
                text = text.replace(long_word, separator.join(short_words))

        messages = []
        count2 = 0
        for word in text.split(separator):
            if (messages and len(
                    (messages[count2] + word).replace(separator, '').replace(' ', '')) > split_message_length * (
                    39 / 40)):
                count2 += 1
            if count2 >= len(messages):
                messages.append('')
            messages[count2] += word + separator

        insert_code_block, insert_code_line = None, None
        for j in range(len(messages)):
            if insert_code_block:
                messages[j] = insert_code_block + messages[j]
                insert_code_block = None
            elif insert_code_line:
                messages[j] = insert_code_line + messages[j]
                insert_code_line = None

            code_blocks = re.findall('```[\\S]*\\n|```', messages[j], re.MULTILINE)
            code_lines = re.findall('[^`]`{1,2}[^`]|[^`]`{1,2}[^`]{0,1}', messages[j], re.MULTILINE)

            if code_blocks and len(code_blocks) % 2 == 1:
                messages[j] += "```"
                insert_code_block = code_blocks[-1] + '\n'
            elif code_lines and len(code_lines) % 2 == 1:
                insert_code_line = ''.join(c for c in code_lines[-1] if c == '`')
                messages[j] += insert_code_line

        return messages[:self.settings['amounts']['maxMessages']] if self.settings['amounts'][
            'maxMessages'] else messages
