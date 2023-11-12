from datetime import datetime, timezone
from functools import cached_property
from typing import Tuple

import disnake
from disnake.ext import commands

import features.report as report_features
import utils
from buttons.base import BaseView
from config.app_config import config
from config.messages import Messages
from database.report import AnswerDB, ReportDB
from permissions import permission_check


class ReportView(BaseView):
    def __init__(self):
        super().__init__(timeout=None)

    @cached_property
    def report_channel(self) -> disnake.ForumChannel:
        return self.bot.get_channel(config.report_channel)

    async def set_view_resolved(self, embed: dict, author_id: int, report_id: int) -> disnake.Embed:
        """set the report as resolved or not resolved"""
        report = ReportDB.get_report(report_id)

        if report.resolved:
            embed = await report_features.embed_resolved(self, "Anonym", embed, report.type, False)
            report.set_resolved(report_id, author_id, False)
        else:
            embed = await report_features.embed_resolved(self, "Anonym", embed, report.type, True)
            report.set_resolved(report_id, author_id, True)
        return embed

    async def get_report_author(self, inter: disnake.MessageInteraction) -> disnake.User:
        """get the report author object from the report id"""
        report_id = report_features.extract_report_id(inter)
        report_author_id = ReportDB.get_report_author(report_id)
        report_author = await self.bot.get_or_fetch_user(report_author_id)
        return report_author

    async def set_spam(
        self,
        button: disnake.ui.Button,
        inter: disnake.MessageInteraction,
        report: ReportDB
    ) -> Tuple[str, disnake.Embed]:
        """Set the report as spam, change buttons and tag thread as spam"""
        resolved_author = f"{inter.author.mention} @{inter.author.name}"
        embed = inter.message.embeds[0].to_dict()

        if report.fake_report:
            ReportDB.set_fake_report(report.id, inter.author.id, False)
            for child in self.children:
                if child.custom_id == "report:resolve":
                    embed = await report_features.embed_resolved(
                        self, resolved_author, embed, report.type, False
                    )
            button.label = "Mark spam"
            button.style = disnake.ButtonStyle.red
            message = Messages.report_message_not_spam(id=report.id, author=inter.author.name)
            await report_features.set_tag(self.report_channel, inter.message.channel, "open")

        else:
            ReportDB.set_fake_report(report.id, inter.author.id, True)
            for child in self.children:
                if child.custom_id == "report:resolve":
                    embed = await report_features.embed_resolved(
                        self, resolved_author, embed, "Spam", True
                    )
                    child.disabled = True
            button.disabled = False
            button.label = f"Spam marked by @{inter.author.name}"
            button.style = disnake.ButtonStyle.primary
            message = Messages.report_message_spam(id=report.id, author=inter.author.name)
            await report_features.set_tag(self.report_channel, inter.message.channel, "spam")
        return message, embed

    async def interaction_check(self, inter: disnake.Interaction) -> bool:
        return permission_check.submod_plus(inter)

    @disnake.ui.button(
        label="Resolve",
        emoji="❌",
        style=disnake.ButtonStyle.secondary,
        custom_id="report:resolve"
    )
    async def resolve(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        await inter.response.defer()
        report_author = await self.get_report_author(inter)
        report_id = report_features.extract_report_id(inter)
        report = ReportDB.get_report(report_id)
        embed = inter.message.embeds[0].to_dict()
        resolved_by = f"{inter.author.mention} @{inter.author.name}"

        if report.resolved:
            embed = await report_features.embed_resolved(self, resolved_by, embed, report.type, False)
            report.set_resolved(report_id, inter.author.id, False)
            await report_features.set_tag(self.report_channel, inter.message.channel, "open")
            await report_author.send(Messages.report_unresolved(id=report_id, author=inter.author.name))
            await inter.message.channel.send(
                Messages.report_unresolved(id=report_id, author=inter.author.name)
            )
        else:
            embed = await report_features.embed_resolved(self, resolved_by, embed, report.type, True)
            report.set_resolved(report_id, inter.author.id, True)
            await report_features.set_tag(self.report_channel, inter.message.channel, "resolved")

        # dont send image to user
        embed_user = embed.copy()
        embed_user.set_image(url=None)

        await report_author.send(embed=embed_user)
        await inter.message.channel.send(embed=embed)
        await inter.edit_original_response(embed=embed, view=self, attachments=None)

    @disnake.ui.button(
        label="Send answer",
        emoji="✉️",
        style=disnake.ButtonStyle.secondary,
        custom_id="report:answer"
    )
    async def answer(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        report_id = report_features.extract_report_id(inter)
        await inter.response.send_modal(modal=ReportAnswerModal(self, self.bot, inter, report_id))

    @disnake.ui.button(
        label="Mark spam",
        emoji="⚠️",
        style=disnake.ButtonStyle.red,
        custom_id="report:spam"
    )
    async def spam(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        """The report is a spam"""
        await inter.response.defer()
        report_id = report_features.extract_report_id(inter)
        report = ReportDB.get_report(report_id)
        report_author = await self.get_report_author(inter)
        report_message = await report_features.convert_url(inter, report.report_url)
        message, embed = await self.set_spam(button, inter, report)

        await report_author.send(message)
        await report_message.channel.send(message)
        await inter.edit_original_response(embed=embed, view=self)


class ReportGeneralView(ReportView):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot


class ReportMessageView(ReportView):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    @disnake.ui.button(
        label="Delete reported message",
        emoji="🗑",
        style=disnake.ButtonStyle.red,
        custom_id="report:delete"
    )
    async def delete(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        """The reported message is deleted"""
        await inter.response.defer()
        button.disabled = True
        report_id = report_features.extract_report_id(inter)
        report = ReportDB.get_report(report_id)
        message_url = ReportDB.get_report(report_id).message_url
        message = await report_features.convert_url(inter, message_url)
        report_message = await report_features.convert_url(inter, report.report_url)

        if message is None:
            button.label = "Message not found"
            delete_message = Messages.report_message_already_deleted(author=inter.author.name)
        else:
            button.label = f"Deleted by @{inter.author.name}"
            delete_message = Messages.report_message_deleted(author=inter.author.name)
            await message.delete()

        await report_message.channel.send(delete_message)
        await inter.edit_original_response(view=self)


class ReportAnonymView(BaseView):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    @cached_property
    def report_channel(self) -> disnake.ForumChannel:
        return self.bot.get_channel(config.report_channel)

    async def interaction_check(self, inter: disnake.Interaction) -> bool:
        report_id = report_features.extract_report_id(inter)
        if ReportDB.is_resolved(report_id):
            await inter.message.edit(view=None)
            await inter.send(Messages.report_already_solved(id=report_id), ephemeral=True)
            return False
        return True

    @disnake.ui.button(
        label="Resolve",
        emoji="❌",
        style=disnake.ButtonStyle.secondary,
        custom_id="report:resolve:anonym"
    )
    async def resolve(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        await inter.response.defer()
        report_id = report_features.extract_report_id(inter)
        report = ReportDB.get_report(report_id)
        report_message = await report_features.convert_url(inter, report.report_url)
        embed = report_message.embeds[0].to_dict()

        # remove buttons
        self.children = []

        if report.type == "general":
            view = ReportGeneralView(self.bot)
            embed = await view.set_view_resolved(embed, "", report_id)
        else:
            view = ReportMessageView(self.bot)
            embed = await view.set_view_resolved(embed, "", report_id)

        await report_features.set_tag(self.report_channel, report_message.channel, "resolved")
        await report_message.edit(embed=embed, view=view)
        await report_message.channel.send(embed=embed)
        await inter.edit_original_message(view=None)
        await inter.send(embed=embed)

    @disnake.ui.button(
        label="Send answer",
        emoji="✉️",
        style=disnake.ButtonStyle.secondary,
        custom_id="report:answer:anonym"
    )
    async def answer(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        report_id = report_features.extract_report_id(inter)
        await inter.response.send_modal(modal=ReportAnswerModal(self, self.bot, inter, report_id))
        await inter.edit_original_response(view=self)


class ReportAnswerOnlyView(BaseView):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    async def interaction_check(self, inter: disnake.Interaction) -> bool:
        report_id = report_features.extract_report_id(inter)
        if ReportDB.is_resolved(report_id):
            await inter.message.edit(view=None)
            await inter.send(Messages.report_already_solved(id=report_id), ephemeral=True)
            return False
        return permission_check.submod_plus(inter)

    @disnake.ui.button(
        label="Send answer",
        emoji="✉️",
        style=disnake.ButtonStyle.secondary,
        custom_id="report:answer:only"
    )
    async def answer(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        report_id = report_features.extract_report_id(inter)
        await inter.response.send_modal(modal=ReportAnswerModal(self, self.bot, inter, report_id))
        await inter.edit_original_message(view=self)


class ReportAnswerModal(disnake.ui.Modal):
    def __init__(self, view, bot: commands.Bot, inter: disnake.MessageInteraction, report_id: int) -> None:
        self.view = view
        self.bot = bot
        self.inter = inter
        self.report_id = report_id
        self.title = Messages.report_answer_title(id=report_id)
        components = [
            disnake.ui.TextInput(
                label=self.title,
                placeholder=Messages.report_answer,
                custom_id="answer",
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

    def answer_embed(self, inter: disnake.ModalInteraction, report: ReportDB, answer: str) -> disnake.Embed:
        """creates an embed template for the submitted answer"""
        description = Messages.report_embed_answered(last_answer=report.last_answer, answer=answer)
        embed = disnake.Embed(
            title=self.title.format(id=report.id),
            description=description,
            color=disnake.Color.yellow()
        )

        if inter.channel.type == disnake.ChannelType.private:
            author = "Anonym"
            embed.timestamp = datetime.now(tz=timezone.utc)
            embed.set_footer(
                icon_url=inter.author.default_avatar.url,
                text=f"{author} | ID: {report.id}"
            )

        else:
            author = f"{inter.author.mention} @{inter.author.name}"
            utils.add_author_footer(embed, inter.author, additional_text=[f"ID: {report.id}"])

        embed.add_field(name="Answered by", value=author, inline=False)
        return embed

    async def callback(self, inter: disnake.ModalInteraction) -> None:
        # respond to interaction to prevent timeout
        await inter.send(Messages.report_answer_success, ephemeral=True)

        answer = inter.text_values['answer']
        report = ReportDB.get_report(self.report_id)
        report_author = await self.bot.get_or_fetch_user(report.author_id)
        report_message = await report_features.convert_url(inter, report.report_url)
        embed = self.answer_embed(inter, report, answer)
        AnswerDB.add_answer(self.report_id, inter.author.id, answer)

        if inter.channel.type == disnake.ChannelType.private:
            # interaction in DMs
            await report_message.channel.send(embed=embed, view=ReportAnswerOnlyView(self.bot))
            await inter.message.edit(view=None)
        else:
            # interaction in forum thread
            await report_message.channel.send(embed=embed)

        await report_author.send(embed=embed, view=ReportAnonymView(self.bot))
