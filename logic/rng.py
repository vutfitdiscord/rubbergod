from random import randint, choice

import utils
from config.messages import Messages


class Rng:
    @staticmethod
    def pick_option(message):
        """"Pick one option from message"""
        if "?" in message:
            message = message.split('?', 1)[1]

        options = message.split()
        if len(options) > 0:
            return choice(options)
        else:
            return False

    @staticmethod
    def generate_number(message):
        """"Generate random number from interval"""
        string = message.content.split(" ")
        if len(string) != 3 and len(string) != 2:
            return Messages.rng_generator_format
        try:
            x = int(string[1])
            if len(string) == 3:
                y = int(string[2])
            else:
                y = 0
        except ValueError:
            return utils.fill_message("rng_generator_format_number", user=message.author.id)
        if x > y:
            x, y = y, x  # variable values swap
        return randint(x, y)

    @staticmethod
    def flip():
        return choice(["True", "False"])
