from functools import cached_property

import disnake
from disnake.ext import commands

import features.report as report_features
import utils
from buttons.report import ReportGeneralView, ReportMessageView
from config.app_config import config
from config.messages import Messages
from database.report import ReportDB, UserDB


class ReportModal(disnake.ui.Modal):
    def __init__(
        self,
        bot: commands.Bot,
        dm_message: disnake.Message,
        title="General report",
        message: disnake.Message = None
    ) -> None:
        self.bot = bot
        self.dm_message = dm_message
        self.title = title
        self.message = message
        components = [
            disnake.ui.TextInput(
                label="Report reason",
                placeholder=Messages.report_modal_placeholder,
                custom_id="reason",
                style=disnake.TextInputStyle.long,
                required=True,
                max_length=2000,
            )
        ]

        super().__init__(
            title=self.title,
            custom_id="report_modal",
            timeout=900,
            components=components
        )

    def report_embed(
        self,
        inter: disnake.ModalInteraction,
        report_reason: str,
        report_id: int
    ) -> disnake.Embed:
        """creates an embed template for the report"""
        embed = disnake.Embed(
            title=self.title,
            description=report_reason,
            color=disnake.Color.red()
        )

        if isinstance(self.message, disnake.Message):
            embed.add_field(name="Message", value=f"{self.message.jump_url}\n{self.message.channel.name}")
            embed.add_field(
                name="Reported user",
                value=f"{self.message.author.mention}\n@{self.message.author}"
            )
        embed.add_field(name="Resolved by", value="---", inline=False)

        utils.add_author_footer(
            embed=embed,
            author=inter.author,
            additional_text=[f"ID: {report_id}"],
            anonymous=True
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

    async def report_general(self, inter: disnake.ModalInteraction) -> None:
        """add general report to db and send it to the report room"""
        report_reason = inter.text_values['reason']
        UserDB.add_user(inter.author.id)
        report_id = ReportDB.add_report(type="general", author_id=inter.author.id, reason=report_reason)

        embed = self.report_embed(inter, report_reason, report_id)

        _, message = await self.report_channel.create_thread(
            name=f"Report #{report_id}",
            embed=embed,
            view=ReportGeneralView(self.bot)
        )

        await message.pin()
        await report_features.set_tag(self.report_channel, message.channel, "open")
        ReportDB.set_report_url(report_id, message.jump_url)
        await self.dm_message.edit(content="", embed=embed)
        await inter.send(Messages.report_modal_success, ephemeral=True)

    async def report_message(self, inter: disnake.ModalInteraction) -> None:
        """add message report to db and send it to the report room"""
        report_reason = Messages.report_message_embed(
            content=self.message.content,
            reason=inter.text_values['reason']
        )
        UserDB.add_user(inter.author.id)
        report_id = ReportDB.add_report(
            type="message",
            author_id=inter.author.id,
            reason=inter.text_values['reason'],
            message_url=self.message.jump_url,
            target_user_id=self.message.author.id
        )

        embed = self.report_embed(inter, report_reason, report_id)

        _, message = await self.report_channel.create_thread(
            name=f"Report #{report_id} - {self.message.author}",
            embed=embed,
            view=ReportMessageView(self.bot)
        )

        await message.pin()
        await report_features.set_tag(self.report_channel, message.channel, "open")
        ReportDB.set_report_url(report_id, message.jump_url)
        await self.dm_message.edit(content="", embed=embed)
        await inter.send(Messages.report_modal_success, ephemeral=True)
