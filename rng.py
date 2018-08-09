from random import randint


class Rng:

	def pick_option(self, message):
		""""Pick one option from message"""
		split = message.content.split()
		if len(split) > 2:
			if "?" in split:
				separatorIndex = split.index("?")
				if separatorIndex:
					if ((len(split) - 1) - (separatorIndex + 1)) > 0:
						return split[randint(separatorIndex + 1, len(split) - 1)]
			else:
				return split[randint(1, len(split) - 1)]
		return False

	def generate_number(self, message):
		""""Generate random number from interval"""
		string = message.content.split(" ")
		x = int(string[1])
		y = int(string[2])
		if x > y:
			x, y = y, x  # variable values swap
		return randint(x, y)

	def flip(self):
		return "True" if randint(0, 1) else "False"