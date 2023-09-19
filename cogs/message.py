"""
Cog for sending and managing messages sent by bot.
"""


import disnake
from disnake.ext import commands

from cogs.base import Base
from config import cooldowns
from config.messages import Messages
from modals.message import MessageModal
from permissions import permission_check


class Message(Base, commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @commands.check(permission_check.submod_plus)
    @cooldowns.default_cooldown
    @commands.slash_command(name="message")
    async def message(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @message.sub_command(name="send", description=Messages.message_send_brief)
    async def send(
        self,
        inter: disnake.ApplicationCommandInteraction,
        channel: disnake.TextChannel = commands.Param(description=Messages.message_channel_brief),
    ):
        message_modal = MessageModal(self.bot, title="Send message", channel=channel)
        await inter.response.send_modal(modal=message_modal)

    @message.sub_command(name="resend", description=Messages.message_resend_brief)
    async def resend(
        self,
        inter: disnake.ApplicationCommandInteraction,
        channel: disnake.TextChannel = commands.Param(description=Messages.message_channel_brief),
        message_url: str = commands.Param(description=Messages.message_url_brief),
    ):
        try:
            message: disnake.Message = await commands.MessageConverter().convert(inter, message_url)
        except commands.MessageNotFound:
            await inter.send(Messages.message_not_found, ephemeral=True)
            return
        if len(message.content) > 2000:
            await inter.send(Messages.message_too_long, ephemeral=True)
            return
        await inter.send(Messages.message_sent(channel=channel.mention), ephemeral=True)
        await channel.send(message.content)

    @message.sub_command(name="edit", description=Messages.message_edit_brief)
    async def edit(
        self,
        inter: disnake.ApplicationCommandInteraction,
        message_url: str = commands.Param(description=Messages.message_url_brief)
    ):
        try:
            message: disnake.Message = await commands.MessageConverter().convert(inter, message_url)
        except commands.MessageNotFound:
            await inter.send(Messages.message_not_found, ephemeral=True)
            return
        if len(message.content) > 2000:
            await inter.send(Messages.message_too_long, ephemeral=True)
            return
        message_modal = MessageModal(self.bot, title="Edit message", message=message, edit=True)
        await inter.response.send_modal(modal=message_modal)


def setup(bot):
    bot.add_cog(Message(bot))
