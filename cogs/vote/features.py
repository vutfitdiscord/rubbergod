import re

import emoji
from dateutil import parser

from utils import is_command_message


class VoteMessage:
    class VoteOption:
        def __init__(self, emoji: str, is_unicode: bool, message: str, count: int):
            self.emoji = emoji
            self.message = message
            self.count = count
            self.is_unicode = is_unicode

    class ParseError(Exception):
        pass

    class NotEmojiError(Exception):
        pass

    emoji_regex = re.compile("^<:.*:([0-9]+)>(.+)")

    @classmethod
    def parse_option(cls, opt_line: str) -> VoteOption:
        matches = cls.emoji_regex.match(opt_line)
        if matches is None:
            # it is not a disnake emoji, try unicode
            emojis = emoji.emoji_list(opt_line)
            if len(emojis) > 0 and emojis[0]["match_start"] == 0:
                opt_emoji = emojis[0]["emoji"]
                opt_message = opt_line[len(opt_emoji) :].strip()
            else:
                raise cls.NotEmojiError(opt_line)
        else:
            opt_emoji = matches.group(1)
            opt_message = matches.group(2).strip()

        return cls.VoteOption(opt_emoji, matches is None, opt_message, 0)

    def __init__(self, message: str, is_one_of: bool):
        self.is_one_of = is_one_of
        if is_command_message("vote", message) or is_command_message("singlevote", message):
            message = message[(message.index("vote") + 4) :]

        # If date/time line is present:
        # line 1: date
        # line 2: question
        # lines 3,4..n: emoji option
        if len(message.strip()) == 0:
            raise self.ParseError()
        lines = message.splitlines(False)
        if len(lines) < 3:
            raise self.ParseError()

        try:
            self.end_date = parser.parse(lines[0], dayfirst=True, fuzzy=True)
            lines = lines[1:]  # Only keep lines with the question and the options
        except parser.ParserError:
            self.end_date = None
            # The user might have actually followed the help and put a newline before the question
            if len(lines[0].strip()) == 0:
                lines = lines[1:]

        if len(lines) < 3:  # Do we still have at least the question and two options?
            raise self.ParseError()

        self.question = lines[0]
        parsed_opts = [self.parse_option(x.strip()) for x in lines[1:]]
        self.options: dict[str, "VoteMessage.VoteOption"] = {x.emoji: x for x in parsed_opts}
        # Check if emojis are unique
        if len(self.options) != len(set(self.options.keys())):
            raise self.ParseError()
