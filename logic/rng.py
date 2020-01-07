from datetime import date
from random import randint, choice

import utils
from utils import fill_message
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
            return fill_message("rng_generator_format_number", user=message.author.id)
        if x > y:
            x, y = y, x  # variable values swap
        return randint(x, y)

    @staticmethod
    def flip():
        return choice(["True", "False"])

    @staticmethod
    def week():
        starting_week = 38  # School started at 5th week (winter in 37)
        week = date.today().isocalendar()[1]  # get actual week number
        stud_week = week - starting_week
        odd = "Lichý"
        even = "Sudý"
        cal_type = even if week % 2 == 0 else odd
        stud_type = even if stud_week % 2 == 0 else odd
        return "Cal\t{}\t{}\nStd\t{}\t{}".format(cal_type, week,
                                                 stud_type, stud_week)
