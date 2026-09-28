"""
Cog for collecting users who opted-out
"""
import disnake
from disnake.ext import commands

from database.opt_out import OptOutDb
from .messages_cz import MessagesCZ
from cogs.base import Base

class OptOut(Base, commands.Cog):
    @commands.slash_command(name="opt-out", brief=MessagesCZ.opt_out_brief)
    async def _opt_out(self, inter):
        pass

    @_opt_out.sub_command(name="add", brief=MessagesCZ.add_brief)
    async def _opt_out_add(self, inter: disnake.ApplicationCommandInteraction):
        OptOutDb.create(str(inter.author.id))

    @_opt_out.sub_command(name="remove", brief=MessagesCZ.remove_brief)
    async def _opt_out_remove(self, inter: disnake.ApplicationCommandInteraction):
        OptOutDb.remove(str(inter.author.id))
