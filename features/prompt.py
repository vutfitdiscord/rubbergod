import discord
from discord.ext import commands
from collections import OrderedDict
import asyncio

class PromptSession:
	def __init__(self, bot:commands.Bot, ctx:commands.Context, message:str, timeout=60, color=discord.Color.orange()):
		self.bot = bot
		self.ctx = ctx

		self.message = message
		self.color = color
		self.timeout = timeout

		self.__running = False
		self.__prompt_instance = None

		self.reactions = OrderedDict(
			{
				"✅": True,
				"❌": False
			}
		)

	async def __show_prompt(self):
		if self.__running: return False

		em = discord.Embed(title="Confirmation prompt", color=self.color)
		em.description = self.message

		self.__running = True
		self.__prompt_instance = await self.ctx.send(embed=em)

		for react in self.reactions.keys():
			await self.__prompt_instance.add_reaction(react)

		return True

	def __react_check(self, reaction, user):
		if reaction.message.id != self.__prompt_instance.id:
			return False  # not the same message
		if user.id != self.ctx.author.id:
			return False  # not the same user
		if reaction.emoji in self.reactions.keys():
			return True  # reaction was one of the pagination emojis

	async def run(self):
		if not await self.__show_prompt(): return

		try:
			# waits for reaction using react_check
			reaction, user = await self.ctx.bot.wait_for('reaction_add', check=self.__react_check, timeout=self.timeout)
		except asyncio.TimeoutError:
			try:
				await self.__close()
			finally:
				return False
		else:
			try:
				await self.__prompt_instance.remove_reaction(reaction, user)
			except:
				pass

			await self.__close()
			return self.reactions[reaction.emoji]

	async def __close(self):
		self.__running = False
		try:
			await asyncio.sleep(1)
			await self.__prompt_instance.delete()
		except:
			pass