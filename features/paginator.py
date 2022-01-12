import discord
from discord.ext.commands import Context
from collections import OrderedDict
import asyncio
from typing import Union

class PaginatorSession:
	def __init__(self, bot, ctx:Context, timeout=60, pages=None, color=discord.Color.green(),
				 footer:Union[str, None]=None, bot_author:bool=False, delete_after:bool=True):
		self.bot = bot

		self.footer = footer  # footer message
		self.ctx = ctx  # ctx
		self.timeout = timeout  # when the reactions get cleared, int[seconds]
		self.pages = pages  # the list of embeds list[discord.Embed, discord.Embed]
		self.running = False  # currently running, bool
		self.message = None  # current message being paginated, discord.Message
		self.current = 0  # current page index, int
		self.color = color  # embed color
		self.bot_author = bot_author
		self.delete_after = delete_after

		self.reactions = OrderedDict({
			'⏮': self.__first_page,
			'◀': self.__previous_page,
			'⏹': self.__close,
			'▶': self.__next_page,
			'⏭': self.__last_page
		})

	def __valid_page(self, index):
		val_check = 0 <= index < len(self.pages)
		return val_check  # checks if input index is valid

	async def __show_page(self, index: int):
		if not self.__valid_page(index):
			return  # checks for a valid page

		self.current = index
		page = self.pages[index]  # gets the page
		if self.footer is not None:
			page.set_footer(text=self.footer)  # sets footer

		if self.bot_author:
			page.set_author(name=f'{index + 1}/{len(self.pages)}', icon_url=self.bot.user.avatar_url)
		else:
			page.set_author(name=f'{index + 1}/{len(self.pages)}')

		if self.running:
			# if the first embed was sent, it edits it
			await self.message.edit(embed=page)
		else:
			self.running = True
			# sends the message
			self.message = await self.ctx.send(embed=page)

			# adds reactions
			for reaction in self.reactions.keys():
				if len(self.pages) <= 2 and reaction in '⏮⏭':
					continue  # ignores 2 page embed first and last emojis
				if len(self.pages) == 1 and reaction != '⏹':
					continue
				await self.message.add_reaction(reaction)

	def __react_check(self, reaction, user):
		if reaction.message.id != self.message.id:
			return False  # not the same message
		if user.id != self.ctx.author.id:
			return False  # not the same user
		if reaction.emoji in self.reactions.keys():
			return True  # reaction was one of the pagination emojis

	async def run(self):
		if not self.running:
			await self.__show_page(0)

		while self.running:
			try:
				# waits for reaction using react_check
				reaction, user = await self.ctx.bot.wait_for('reaction_add',
				                                             check=self.__react_check,
				                                             timeout=self.timeout)
				try:
					await self.message.remove_reaction(reaction, user)
				except:
					pass

				action = self.reactions[reaction.emoji]
				await action()
			except asyncio.TimeoutError:
				self.running = False
				try:
					await self.__close()
				finally:
					break

	async def __first_page(self):
		if self.current == 0: return
		return await self.__show_page(0)

	async def __last_page(self):
		if self.current == len(self.pages) - 1: return
		return await self.__show_page(len(self.pages) - 1)

	async def __next_page(self):
		return await self.__show_page(self.current + 1)

	async def __previous_page(self):
		return await self.__show_page(self.current - 1)

	async def __close(self):
		self.running = False
		try:
			await self.message.clear_reactions()
			await asyncio.sleep(5)

			if self.delete_after:
				await self.message.delete()
		except:
			pass
