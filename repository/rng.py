from config import messages
from random import randint
from datetime import date
import utils


class Rng:
    @staticmethod
    def pick_option(message):
        """"Pick one option from message"""
        msg = str(message.content)
        if "?" not in msg:
            return False

        options = msg[(msg.index("?") + 1):].split()
        if len(options) > 0:
            return options[randint(0, len(options) - 1)]
        else:
            return False

    def generate_number(self, message):
        """"Generate random number from interval"""
        m = messages.Messages
        string = message.content.split(" ")
        if len(string) != 3 and len(string) != 2:
            return m.rng_generator_format
        try:
            x = int(string[1])
            if len(string) == 3:
                y = int(string[2])
            else:
                y = 0
        except ValueError:
            return m.rng_generator_format_number.format(
                user=utils.generate_mention(message.author.id))
        if x > y:
            x, y = y, x  # variable values swap
        return randint(x, y)

    @staticmethod
    def flip():
        return "True" if randint(0, 1) else "False"

    @staticmethod
    def week():
        starting_week = 5  # School started at 5th week (winter in 37)
        week = date.today().isocalendar()[1]  # get actual week number
        stud_week = week - starting_week
        odd = "Lichý"
        even = "Sudý"
        cal_type = even if week % 2 == 0 else odd
        stud_type = even if stud_week % 2 == 0 else odd
        return "Cal\t{}\t{}\nStd\t{}\t{}".format(cal_type, week,
                                                 stud_type, stud_week)
