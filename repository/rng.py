from random import randint
from datetime import date


class Rng:

	@staticmethod
	def pick_option(message):
		""""Pick one option from message"""
		split = message.content.split()
		if len(split) > 2:
			if "?" in split:
				imdex = split.index("?")
				if imdex:
					if ((len(split) - 1) - (imdex + 1)) > 0:
						return split[randint(imdex + 1, len(split) - 1)]
			else:
				return split[randint(1, len(split) - 1)]
		return False

	@staticmethod
	def generate_number(message):
		""""Generate random number from interval"""
		string = message.content.split(" ")
		x = int(string[1])
		y = int(string[2])
		if x > y:
			x, y = y, x  # variable values swap
		return randint(x, y)

	@staticmethod
	def flip():
		return "True" if randint(0, 1) else "False"

	@staticmethod
	def week():
		week = date.today().isocalendar()[1]  # get actual week number
		if week % 2 == 0:
			return "Sudý kal, lichý stud"
		else:
			return "Lichý kal, sudý stud"
