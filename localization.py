import json
import glob

import config

LANGUAGES = {}

for filename in glob.glob("./langs/[a-z][a-z].json"):
    with open(filename, "r") as f:
        LANGUAGES[filename.split(".")[0]] = json.load(f)


class Language:
    def __init__(self, language="en", fallback=None):
        if language not in LANGUAGES:
            raise NameError(language)

        self.data = LANGUAGES[language]
        self.fallback = fallback

    def __getattr__(self, name):
        if name not in self.data:
            if not self.fallback:
                raise KeyError(name)

            return getattr(self.fallback, name)

        return self.data[name]

    def format(self, name, **keys):
        string = getattr(self, name)

        return string.format(**keys)


locale = Language(
    config.language, fallback=None if config.language == "en" else Language("en")
)
