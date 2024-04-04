from functools import cached_property

import disnake
from disnake.ext import commands

import utils
from cogs.report.views import ReportGeneralView, ReportMessageView
from config.app_config import config
from database.report import ReportDB, UserDB

from . import features as report_features
from .messages_cz import MessagesCZ


class Modal(disnake.ui.Modal):
    def __init__(
        self,
        bot: commands.Bot,
        dm_message: disnake.Message,
        title="General report",
        message: disnake.Message = None,
    ) -> None:
        self.bot = bot
        self.dm_message = dm_message
        self.title = title
        self.message = message
        components = [
            disnake.ui.TextInput(
                label="Report reason",
                placeholder=MessagesCZ.modal_placeholder,
                custom_id="reason",
                style=disnake.TextInputStyle.long,
                required=True,
                max_length=2000,
            )
        ]

        super().__init__(title=self.title, custom_id="report_modal", timeout=900, components=components)

    def report_embed(
        self,
        inter: disnake.ModalInteraction,
        report_reason: str,
        report_id: int,
        first_image: disnake.File = None,
    ) -> disnake.Embed:
        """creates an embed template for the report"""
        embed = disnake.Embed(title=self.title, description=report_reason, color=disnake.Color.red())

        if isinstance(self.message, disnake.Message):
            embed.add_field(name="Message", value=f"{self.message.jump_url}\n{self.message.channel.name}")
            embed.add_field(
                name="Reported user", value=f"{self.message.author.mention}\n`@{self.message.author.name}`"
            )
            if first_image is not None:
                embed.set_image(file=first_image)

        embed.add_field(name="Resolved by", value="---", inline=False)

        utils.add_author_footer(
            embed=embed, author=inter.author, additional_text=[f"ID: {report_id}"], anonymous=True
        )
        return embed

    @cached_property
    def report_channel(self) -> disnake.ForumChannel:
        return self.bot.get_channel(config.report_channel)

    async def callback(self, inter: disnake.ModalInteraction) -> None:
        if isinstance(self.message, disnake.Message):
            await self.report_message(inter)
        else:
            await self.report_general(inter)

    async def edit_or_send(self, inter: disnake.ModalInteraction, embed: disnake.Embed):
        """edit or send embed to the user depends if user deleted the message or not"""
        url = self.dm_message.jump_url
        try:
            message: disnake.Message = await commands.MessageConverter().convert(inter, url)
            await message.edit(content="", embed=embed, view=None)
        except commands.MessageNotFound:
            await message.channel.send(content="", embed=embed, view=None)

    async def report_general(self, inter: disnake.ModalInteraction) -> None:
        """add general report to db and send it to the report room"""
        await inter.send(MessagesCZ.modal_success, ephemeral=True)
        report_reason = inter.text_values["reason"]
        UserDB.add_user(inter.author.id)
        report_id = ReportDB.add_report(type="general", author_id=inter.author.id, reason=report_reason)

        embed = self.report_embed(inter, report_reason, report_id)

        _, message = await self.report_channel.create_thread(
            name=f"Report #{report_id}", embed=embed, view=ReportGeneralView(self.bot)
        )

        await message.pin()
        await report_features.set_tag(self.report_channel, message.channel, "open")
        ReportDB.set_report_url(report_id, message.jump_url)

        await self.edit_or_send(inter, embed)

    async def report_message(self, inter: disnake.ModalInteraction) -> None:
        """add message report to db and send it to the report room"""
        await inter.send(MessagesCZ.modal_success, ephemeral=True)

        if not self.message:
            await inter.send(MessagesCZ.message_not_found, ephemeral=True)
            return

        report_reason = MessagesCZ.message_embed(
            content=self.message.content, reason=inter.text_values["reason"]
        )
        UserDB.add_user(inter.author.id)
        report_id = ReportDB.add_report(
            type="message",
            author_id=inter.author.id,
            reason=inter.text_values["reason"],
            message_url=self.message.jump_url,
            target_user_id=self.message.author.id,
        )

        images, files, attachments_too_big = await utils.parse_attachments(self.message)

        first_image = None
        if images:
            first_image = images[0]
            images.pop(0)

        embed = self.report_embed(inter, report_reason, report_id, first_image)

        thread, message = await self.report_channel.create_thread(
            name=f"Report #{report_id} - `{self.message.author.name}`",
            embed=embed,
            view=ReportMessageView(self.bot),
        )

        if attachments_too_big:
            attachments_too_big = [
                f"[{attachment.filename}]({attachment.url})" for attachment in attachments_too_big
            ]
        if any(inner_list for inner_list in [images, files, attachments_too_big]):
            # if there are any attachments combine them
            files = images + files if files + images else []
            content = ""

            if attachments_too_big:
                content = MessagesCZ.attachment_too_big(files="\n- ".join(attachments_too_big))

            await thread.send(content=content, files=files)

        # remove image from embed because of explicit content
        embed.set_image(url=None)

        await message.pin()
        await report_features.set_tag(self.report_channel, message.channel, "open")
        ReportDB.set_report_url(report_id, message.jump_url)

        await self.edit_or_send(inter, embed)
