from functools import cached_property

import disnake

from buttons.base import BaseView
from config.app_config import config
from database.report import AnswerDB, ReportDB
from permissions import permission_check
from rubbergod import Rubbergod

from . import features as report_features
from .features_errors import ButtonInteractionError
from .messages_cz import MessagesCZ


class ReportView(BaseView):
    def __init__(self):
        super().__init__(timeout=None)

    @cached_property
    def report_channel(self) -> disnake.ForumChannel:
        return self.bot.get_channel(config.report_channel)

    async def interaction_check(self, inter: disnake.Interaction) -> bool:
        return permission_check.submod_plus(inter, raise_exception=False)

    async def set_view_resolved(
        self, embed_dict: dict, author_id: str, report_id: int
    ) -> disnake.Embed | None:
        """set the report as resolved or not resolved"""
        report = ReportDB.get_report(report_id)

        if not report:
            return None

        if report.resolved:
            embed = await report_features.embed_resolved(
                self.children, "Anonym", embed_dict, report.type, False
            )
            report.set_resolved(report_id, author_id, False)
        else:
            embed = await report_features.embed_resolved(
                self.children, "Anonym", embed_dict, report.type, True
            )
            report.set_resolved(report_id, author_id, True)
        return embed

    async def get_report_author(self, report_id: int) -> disnake.User:
        """get the report author object from the report id"""
        report_author_id = ReportDB.get_report_author(report_id)
        report_author = await self.bot.get_or_fetch_user(report_author_id)
        return report_author

    async def set_spam(
        self, button: disnake.ui.Button, inter: disnake.MessageInteraction, report: ReportDB
    ) -> tuple[str, disnake.Embed]:
        """Set the report as spam, change buttons and tag thread as spam"""
        resolved_author = f"{inter.author.mention} `@{inter.author.name}`"
        embed_dict = inter.message.embeds[0].to_dict()

        if report.fake_report:
            ReportDB.set_fake_report(report.id, inter.author.id, False)
            for child in self.children:
                if child.custom_id == "report:resolve":
                    embed = await report_features.embed_resolved(
                        self.children, resolved_author, embed_dict, report.type, False
                    )
            button.label = "Mark spam"
            button.style = disnake.ButtonStyle.red
            message = MessagesCZ.message_not_spam(
                id=report.id, author=inter.author.mention, author_name=inter.author.name
            )
            await report_features.set_tag(self.report_channel, inter.message.channel, "open")

        else:
            ReportDB.set_fake_report(report.id, inter.author.id, True)
            for child in self.children:
                if child.custom_id == "report:resolve":
                    embed = await report_features.embed_resolved(
                        self.children, resolved_author, embed_dict, "Spam", True
                    )
                    child.disabled = True
            button.disabled = False
            button.label = f"Spam marked by @{inter.author.name}"
            button.style = disnake.ButtonStyle.primary
            message = MessagesCZ.message_spam(
                id=report.id, author=inter.author.mention, author_name=inter.author.name
            )
            await report_features.set_tag(self.report_channel, inter.message.channel, "spam")
        return message, embed

    @disnake.ui.button(
        label="Resolve", emoji="❌", style=disnake.ButtonStyle.secondary, custom_id="report:resolve"
    )
    async def resolve(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        await inter.response.defer()
        report_id = report_features.extract_report_id(inter)
        report_author = await self.get_report_author(report_id)
        report = ReportDB.get_report(report_id)
        embed_dict = inter.message.embeds[0].to_dict()
        resolved_by = f"{inter.author.mention} `@{inter.author.name}`"

        if not report:
            raise ButtonInteractionError(inter.author.mention, MessagesCZ.report_not_found)

        if report.resolved:
            embed = await report_features.embed_resolved(
                self.children, resolved_by, embed_dict, report.type, False
            )
            report.set_resolved(report_id, inter.author.id, False)
            content = MessagesCZ.report_unresolved(
                id=report_id, author=inter.author.mention, author_name=inter.author.name
            )
            await report_features.set_tag(self.report_channel, inter.message.channel, "open")
            await report_author.send(content)
            await inter.message.channel.send(content, allowed_mentions=disnake.AllowedMentions.none())
        else:
            embed = await report_features.embed_resolved(
                self.children, resolved_by, embed_dict, report.type, True
            )
            report.set_resolved(report_id, inter.author.id, True)
            await report_features.set_tag(self.report_channel, inter.message.channel, "resolved")

        # dont send image to user
        embed_user = embed.copy()
        embed_user.set_image(url=None)

        await report_author.send(embed=embed_user)
        await inter.message.channel.send(embed=embed)
        await inter.edit_original_response(embed=embed, view=self, attachments=None)

    @disnake.ui.button(
        label="Send answer", emoji="✉️", style=disnake.ButtonStyle.secondary, custom_id="report:answer"
    )
    async def answer(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        report_id = report_features.extract_report_id(inter)
        await inter.response.send_modal(modal=ReportAnswerModal(self, self.bot, inter, report_id))

    @disnake.ui.button(label="Mark spam", emoji="⚠️", style=disnake.ButtonStyle.red, custom_id="report:spam")
    async def spam(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        """The report is a spam"""
        await inter.response.defer()
        report_id = report_features.extract_report_id(inter)
        report = ReportDB.get_report(report_id)

        if not report:
            raise ButtonInteractionError(inter.author.mention, MessagesCZ.report_not_found)

        report_author = await self.get_report_author(report_id)
        report_message = await report_features.convert_url(inter, report.report_url)
        description, embed = await self.set_spam(button, inter, report)
        title = MessagesCZ.message_spam_title(id=report_id)
        spam_embed = report_features.info_message_embed(inter, report, title, description)

        await report_author.send(embed=spam_embed)
        await report_message.channel.send(embed=spam_embed)
        await inter.edit_original_response(embed=embed, view=self, attachments=None)

    async def on_error(self, error, item: disnake.ui.Item, interaction: disnake.MessageInteraction):
        if isinstance(error, ButtonInteractionError):
            await interaction.send(error.message, ephemeral=error.ephemeral)
            # major error occurred, pass to global handler
        await super().on_error(error, item, interaction)


class ReportGeneralView(ReportView):
    def __init__(self, bot: Rubbergod):
        super().__init__()
        self.bot = bot


class ReportMessageView(ReportView):
    def __init__(self, bot: Rubbergod):
        super().__init__()
        self.bot = bot

    @disnake.ui.button(
        label="Delete reported message", emoji="🗑", style=disnake.ButtonStyle.red, custom_id="report:delete"
    )
    async def delete(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        """The reported message is deleted"""
        await inter.response.defer()
        button.disabled = True
        report_id = report_features.extract_report_id(inter)
        report = ReportDB.get_report(report_id)

        if not report:
            raise ButtonInteractionError(inter.author.mention, MessagesCZ.report_not_found)

        try:
            message = await report_features.convert_url(inter, report.message_url)
        except ButtonInteractionError:
            message = None
        report_message = await report_features.convert_url(inter, report.report_url)
        report_author = await self.get_report_author(report_id)

        try:
            await message.delete()
            button.label = f"Deleted by @{inter.author.name}"
            description = MessagesCZ.message_deleted(
                author=inter.author.mention, author_name=inter.author.name
            )
        except (disnake.NotFound, AttributeError):
            # message is None or already deleted, often it's cached message
            button.label = "Message not found"
            description = MessagesCZ.message_already_deleted(
                author=inter.author.mention, author_name=inter.author.name
            )

        title = MessagesCZ.message_deleted_title(id=report_id)
        embed = report_features.info_message_embed(inter, report, title, description)

        await report_message.channel.send(embed=embed)
        await report_author.send(embed=embed, view=ReportAnonymView(self.bot))
        await inter.edit_original_response(view=self, attachments=None)


class ReportAnonymView(BaseView):
    def __init__(self, bot: Rubbergod):
        super().__init__(timeout=None)
        self.bot = bot

    @cached_property
    def report_channel(self) -> disnake.ForumChannel:
        return self.bot.get_channel(config.report_channel)

    async def interaction_check(self, inter: disnake.Interaction) -> bool:
        report_id = report_features.extract_report_id(inter)
        if ReportDB.is_resolved(report_id):
            await inter.message.edit(view=None)
            await inter.send(MessagesCZ.report_already_solved(id=report_id), ephemeral=True)
            return False
        return True

    @disnake.ui.button(
        label="Resolve", emoji="❌", style=disnake.ButtonStyle.secondary, custom_id="report:resolve:anonym"
    )
    async def resolve(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        await inter.response.defer()
        report_id = report_features.extract_report_id(inter)
        report = ReportDB.get_report(report_id)

        if not report:
            raise ButtonInteractionError(inter.author.mention, MessagesCZ.report_not_found, ephemeral=True)

        report_message = await report_features.convert_url(inter, report.report_url)
        embed_dict = report_message.embeds[0].to_dict()

        if report.type == "general":
            view = ReportGeneralView(self.bot)
        else:
            view = ReportMessageView(self.bot)

        embed = await view.set_view_resolved(embed_dict, "", report_id)

        await report_features.set_tag(self.report_channel, report_message.channel, "resolved")
        await report_message.edit(embed=embed, view=view)
        await report_message.channel.send(embed=embed)
        await inter.edit_original_message(view=None)
        await inter.send(embed=embed)

    @disnake.ui.button(
        label="Send answer", emoji="✉️", style=disnake.ButtonStyle.secondary, custom_id="report:answer:anonym"
    )
    async def answer(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        report_id = report_features.extract_report_id(inter)
        await inter.response.send_modal(modal=ReportAnswerModal(self, self.bot, inter, report_id))
        await inter.edit_original_response(view=self)


class ReportAnswerOnlyView(BaseView):
    def __init__(self, bot: Rubbergod):
        super().__init__(timeout=None)
        self.bot = bot

    async def interaction_check(self, inter: disnake.Interaction) -> bool:
        report_id = report_features.extract_report_id(inter)
        if ReportDB.is_resolved(report_id):
            await inter.message.edit(view=None)
            await inter.send(MessagesCZ.report_already_solved(id=report_id), ephemeral=True)
            return False
        return permission_check.submod_plus(inter)

    @disnake.ui.button(
        label="Send answer", emoji="✉️", style=disnake.ButtonStyle.secondary, custom_id="report:answer:only"
    )
    async def answer(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        report_id = report_features.extract_report_id(inter)
        await inter.response.send_modal(modal=ReportAnswerModal(self, self.bot, inter, report_id))
        await inter.edit_original_message(view=self)


class ReportAnswerModal(disnake.ui.Modal):
    def __init__(self, view, bot: Rubbergod, inter: disnake.MessageInteraction, report_id: int) -> None:
        self.view = view
        self.bot = bot
        self.inter = inter
        self.report_id = report_id
        self.title = MessagesCZ.answer_title(id=report_id)
        components = [
            disnake.ui.TextInput(
                label=self.title,
                placeholder=MessagesCZ.answer_placeholder,
                custom_id="answer",
                style=disnake.TextInputStyle.long,
                required=True,
                max_length=2000,
            )
        ]

        super().__init__(title=self.title, custom_id="report_modal", timeout=900, components=components)

    async def callback(self, inter: disnake.ModalInteraction) -> None:
        # respond to interaction to prevent timeout
        await inter.send(MessagesCZ.answer_success, ephemeral=True)
        answer = inter.text_values["answer"]
        report = ReportDB.get_report(self.report_id)

        if not report:
            raise ButtonInteractionError(inter.author.mention, MessagesCZ.report_not_found, ephemeral=True)

        report_author = await self.bot.get_or_fetch_user(report.author_id)
        report_message = await report_features.convert_url(inter, report.report_url)
        embed = report_features.answer_embed(self.title, inter, report, answer)
        AnswerDB.add_answer(self.report_id, inter.author.id, answer)

        if inter.channel.type == disnake.ChannelType.private:
            # interaction in DMs
            await report_message.channel.send(embed=embed, view=ReportAnswerOnlyView(self.bot))
            await inter.message.edit(view=None)
        else:
            # interaction in forum thread
            await report_message.channel.send(embed=embed)

        await report_author.send(embed=embed, view=ReportAnonymView(self.bot))
