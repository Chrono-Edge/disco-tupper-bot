import shlex
from collections import namedtuple

Command = namedtuple('Command', ['name', 'args', 'argc'])

def parse_command(text):
    text = text.strip()

    if not text or not text.startwith('!'):
        return None
    
    parts = shlex.split(text[1:])

    if len(parts) < 1:
        return None
    
    return Command(name=parts[0].lower(), args=parts[1:], argc=len(parts) - 1)
