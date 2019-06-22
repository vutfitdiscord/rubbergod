from random import randint
from re import match

"""
Syntax:
XdY - rolls X Y-sided dice, if X is omitted it defaults to 1
XdY + Z - rolls X Y-sided dice, then adds Z to the result
XdYdZ - rolls X Y-sided dice, drops Z lowest dice (drops highest dice if using dh)
XdYkZ - rolls X Y-sided dice, keeps Z highest dice and drops rest (keeps lowest dice if using kl)
XdYdhZkW - rolls X Y-sided dice, drops Z highest dice, then keeps W highest dice (used when dropping high+keeping high or dropping low+keeping low)
"""


class RollResult:
	def __init__(self, text="", result=0):
		self.text = text
		self.result = result

class Roll:
	DICE_REGEX = r"^\s*(?:(\d*)[dD](\d+)(?:(d[hl]?)(\d+))?(?:(k[hl]?)(\d+))?|(\d+))\s*$"

	@staticmethod
	def single_roll_dice(match_result, config):
		groups = match_result.groups()

		if groups[6]:
			return RollResult("**" + groups[6] + "**", int(groups[6]))

		text = "("
		result = 0

		dice_count = 1 if (groups[0] == '') else int(groups[0])
		dice_sides = int(groups[1])

		if dice_count == 0 or dice_sides == 0:
			return RollResult("(**0**)", 0)

		if groups[2] and int(groups[3]) >= dice_count: # Drop
			return RollResult("(**0**)", 0)

		if groups[4] and int(groups[5]) <= 0: # Keep
			return RollResult("(**0**)", 0)

		if dice_count > config.max_dice_at_once:
			raise SyntaxError("Příliš moc kostek v jedné skupině, maximum je %s" % config.max_dice_at_once)

		if dice_sides > config.max_dice_sides:
			raise SyntaxError("Příliš moc stěn na kostkách, maximum je %s" % config.max_dice_sides)

		dice = [randint(1, dice_sides) for i in range(dice_count)]

		# Big brain plays incoming

		crossed_indexes = []

		if groups[2] or groups[4]:
			lookup = dict()

			for index, die in enumerate(dice):
				if die not in lookup.keys():
					lookup[die] = [index]
				else:
					lookup[die].append(index)

			crossed_low = 0
			crossed_high = 0

			# DROPPING

			# Drop lowest dice
			if groups[2]=="d" or groups[2] == "dl":
				to_drop = int(groups[3])
				crossed_low += to_drop
				for i in range(1, dice_sides+1):
					length = len(lookup[i]) if i in lookup.keys() else 0
					if length > 0:
						dropping = min(length, to_drop)
						to_drop -= dropping
						crossed_indexes += lookup[i][:dropping]

			# Drop highest dice
			if groups[2]=="dh":
				to_drop = int(groups[3])
				crossed_high += to_drop
				for i in range(dice_sides, 0, -1):
					length = len(lookup[i]) if i in lookup.keys() else 0
					if length > 0:
						dropping = min(length, to_drop)
						to_drop -= dropping
						crossed_indexes += lookup[i][:dropping]

			# KEEPING

			# Keep highest dice, which is functionally the same as dropping lowest dice
			if groups[4]=="k" or groups[4] == "kh":
				to_drop = dice_count-int(groups[5]) - (crossed_low + crossed_high)
				to_skip = crossed_low
				for i in range(1, dice_sides+1):
					length = len(lookup[i]) if i in lookup.keys() else 0
					if length > 0:
						if 0 < to_skip < length:
							if to_drop < length-to_skip:
								crossed_indexes += lookup[i][to_skip:to_skip+to_drop]
								to_drop = 0
							else:
								crossed_indexes += lookup[i][to_skip:]
								to_drop -= length-to_skip
						elif to_skip <= 0:
							dropping = min(length, to_drop)
							to_drop -= dropping
							crossed_indexes += lookup[i][:dropping]
						to_skip -= length

			# Keep lowest dice, which is functionally the same as dropping highest dice
			if groups[4]=="kl":
				to_drop = dice_count-int(groups[5]) - (crossed_low + crossed_high)
				to_skip = crossed_high
				for i in range(dice_sides, 0, -1):
					length = len(lookup[i]) if i in lookup.keys() else 0
					if length > 0:
						if 0 < to_skip < length:
							if to_drop < length-to_skip:
								crossed_indexes += lookup[i][to_skip:to_skip+to_drop]
								to_drop = 0
							else:
								crossed_indexes += lookup[i][to_skip:]
								to_drop -= length-to_skip
						elif to_skip <= 0:
							dropping = min(length, to_drop)
							to_drop -= dropping
							crossed_indexes += lookup[i][:dropping]
						to_skip -= length

		for index, die in enumerate(dice):
			die_text = "__"+str(die)+"__" if die==dice_sides else str(die)
			if index in crossed_indexes:
				text += "~~" + die_text + "~~"
			else:
				text += "**" + die_text + "**"
				result += die
			text += " "

		if dice_count > config.dice_before_collation:
			return RollResult("(***" + str(result) + "***)", result)

		# Remove last character since that is always a space
		return RollResult(text[:-1] + ")", result)

	@staticmethod
	def roll_dice(message, config):
		roll_string = ' '.join(message.content.split(' ')[1:])

		if roll_string == "":
			return """Formát naleznete na https://wiki.roll20.net/Dice_Reference
Implementovány featury podle obsahu:
8. Drop/Keep"""

		results = []
		dice_groups = roll_string.split('+')

		if len(dice_groups) > config.max_dice_groups:
			return "Příliš moc skupin kostek, maximum je %s" % config.max_dice_groups
		
		for index, dice in enumerate(dice_groups):
			result = match(Roll.DICE_REGEX, dice)
			if result: # result found
				try:
					results.append(Roll.single_roll_dice(result, config))
				except SyntaxError as e:
					return str(e)
			else:
				return "Chybný syntax hodu ve skupině %s" % index

		returntext = ' + '.join(r.text for r in results)
		returntext += " = **" + str(sum(r.result for r in results)) + "**"
		return returntext
