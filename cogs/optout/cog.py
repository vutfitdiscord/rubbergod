"""
Cog for collecting users who opted-out
"""

import disnake
from disnake.ext import commands

from cogs.base import Base
from database.opt_out import OptOutDb

from .messages_cz import MessagesCZ


class OptOut(Base, commands.Cog):
    @commands.slash_command(name="opt-out", brief=MessagesCZ.opt_out_brief)
    async def _opt_out(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()

    @_opt_out.sub_command(name="add", brief=MessagesCZ.add_brief)
    async def _opt_out_add(self, inter: disnake.ApplicationCommandInteraction):
        if OptOutDb.exists(str(inter.author.id)):
            await inter.edit_original_response(content=MessagesCZ.add_already_done)
        else:
            OptOutDb.create(str(inter.author.id))
            await inter.edit_original_response(content=MessagesCZ.add_response)

    @_opt_out.sub_command(name="remove", brief=MessagesCZ.remove_brief)
    async def _opt_out_remove(self, inter: disnake.ApplicationCommandInteraction):
        if OptOutDb.exists(str(inter.author.id)):
            OptOutDb.remove(str(inter.author.id))
            await inter.edit_original_response(content=MessagesCZ.remove_response)
        else:
            await inter.edit_original_response(content=MessagesCZ.remove_not_opted_out)
