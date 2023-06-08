import disnake

import features.report as report_features
import utils
from buttons.base import BaseView
from config.messages import Messages
from permissions import permission_check
from repository.database.report import Answer, Report


class ReportView(BaseView):
    def __init__(self):
        super().__init__(timeout=None)

    async def set_view_resolved(self, embed: dict, author_id: int, report_id: int):
        """set the report as resolved or not resolved"""
        report = Report.get_report(report_id)

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
        report_author_id = Report.get_report_author(report_id)
        report_author = await self.bot.get_or_fetch_user(report_author_id)
        return report_author

    async def interaction_check(self, inter: disnake.Interaction):
        return permission_check.submod_plus(inter)

    @disnake.ui.button(
        label="Resolve",
        emoji="❌",
        style=disnake.ButtonStyle.secondary,
        custom_id="report:resolve"
    )
    async def resolve(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.defer()
        report_author = await self.get_report_author(inter)
        report_id = report_features.extract_report_id(inter)
        report = Report.get_report(report_id)
        embed = inter.message.embeds[0].to_dict()
        resolved_by = f"{inter.author.mention} @{inter.author.name}"

        if report.resolved:
            embed = await report_features.embed_resolved(self, resolved_by, embed, report.type, False)
            report.set_resolved(report_id, inter.author.id, False)
        else:
            embed = await report_features.embed_resolved(self, resolved_by, embed, report.type, True)
            report.set_resolved(report_id, inter.author.id, True)

        await report_author.send(embed=embed)
        await inter.message.thread.send(embed=embed)
        await inter.edit_original_response(embed=embed, view=self)

    @disnake.ui.button(
        label="Send answer",
        emoji="✉️",
        style=disnake.ButtonStyle.secondary,
        custom_id="report:answer"
    )
    async def answer(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        report_id = report_features.extract_report_id(inter)
        await inter.response.send_modal(modal=ReportAnswerModal(self, self.bot, inter, report_id))

    @disnake.ui.button(
        label="Mark spam",
        emoji="⚠️",
        style=disnake.ButtonStyle.red,
        custom_id="report:spam"
    )
    async def spam(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        """The report is a spam"""
        await inter.response.defer()
        report_id = report_features.extract_report_id(inter)
        embed = inter.message.embeds[0].to_dict()
        report = Report.get_report(report_id)
        report_author = await self.get_report_author(inter)
        report_message = await report_features.convert_url(inter, report.report_url)
        resolved_author = f"{inter.author.mention} @{inter.author.name}"

        if report.fake_report:
            Report.set_fake_report(report_id, inter.author.id, False)
            for child in self.children:
                if child.custom_id == "report:resolve":
                    embed = await report_features.embed_resolved(
                        self, inter.author.mention, embed, report.type, False
                    )
                child.disabled = False
            button.label = "Mark spam"
            button.style = disnake.ButtonStyle.red
            message = Messages.report_message_not_spam.format(id=report_id, author=inter.author.name)

        else:
            Report.set_fake_report(report_id, inter.author.id, True)
            for child in self.children:
                if child.custom_id == "report:resolve":
                    embed = await report_features.embed_resolved(self, resolved_author, embed, "Spam", True)
                child.disabled = True
            button.disabled = False
            button.style = disnake.ButtonStyle.primary
            button.label = f"Spam marked by @{inter.author.name}"
            message = Messages.report_message_spam.format(id=report_id, author=inter.author.name)

        await report_author.send(message)
        await report_message.thread.send(message)
        await inter.edit_original_response(embed=embed, view=self)


class ReportGeneralView(ReportView):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot


class ReportMessageView(ReportView):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @disnake.ui.button(
        label="Delete reported message",
        emoji="🗑",
        style=disnake.ButtonStyle.red,
        custom_id="report:delete"
    )
    async def delete(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        """The reported message is deleted"""
        await inter.response.defer()
        button.disabled = True
        report_id = report_features.extract_report_id(inter)
        report = Report.get_report(report_id)
        message_url = Report.get_report(report_id).message_url
        message = await report_features.convert_url(inter, message_url)
        report_message = await report_features.convert_url(inter, report.report_url)

        if message is None:
            button.label = "Message not found"
            delete_message = Messages.report_message_already_deleted.format(author=inter.author.name)
        else:
            button.label = f"Deleted by @{inter.author.name}"
            delete_message = Messages.report_message_deleted.format(author=inter.author.name)
            await message.delete()

        await report_message.thread.send(delete_message)
        await inter.edit_original_response(view=self)


class ReportAnonymView(BaseView):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    async def interaction_check(self, inter: disnake.Interaction):
        report_id = report_features.extract_report_id(inter)
        if Report.is_resolved(report_id):
            await inter.message.edit(view=None)
            await inter.send(Messages.report_already_solved.format(id=report_id), ephemeral=True)
            return False
        return True

    @disnake.ui.button(
        label="Resolve",
        emoji="❌",
        style=disnake.ButtonStyle.secondary,
        custom_id="report:resolve:anonym"
    )
    async def resolve(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.defer()
        report_id = report_features.extract_report_id(inter)
        report = Report.get_report(report_id)
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

        await report_message.edit(embed=embed, view=view)
        await report_message.thread.send(embed=embed)
        await inter.edit_original_message(view=None)
        await inter.send(embed=embed)

    @disnake.ui.button(
        label="Send answer",
        emoji="✉️",
        style=disnake.ButtonStyle.secondary,
        custom_id="report:answer:anonym"
    )
    async def answer(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        report_id = report_features.extract_report_id(inter)
        await inter.response.send_modal(modal=ReportAnswerModal(self, self.bot, inter, report_id))
        await inter.edit_original_response(view=self)


class ReportAnswerOnlyView(BaseView):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    async def interaction_check(self, inter: disnake.Interaction):
        return permission_check.submod_plus(inter)

    @disnake.ui.button(
        label="Send answer",
        emoji="✉️",
        style=disnake.ButtonStyle.secondary,
        custom_id="report:answer:only"
    )
    async def answer(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        report_id = report_features.extract_report_id(inter)
        await inter.response.send_modal(modal=ReportAnswerModal(self, self.bot, inter, report_id))
        await inter.edit_original_message(view=self)


class ReportAnswerModal(disnake.ui.Modal):
    def __init__(self, view, bot, inter: disnake.MessageInteraction, report_id: int) -> None:
        self.view = view
        self.bot = bot
        self.inter = inter
        self.report_id = report_id
        self.title = Messages.report_answer_title.format(id=report_id)
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

    def answer_embed(self, inter: disnake.ModalInteraction, report: Report, answer: str) -> disnake.Embed:
        """creates an embed template for the submitted answer"""
        description = Messages.report_embed_answered.format(last_answer=report.last_answer, answer=answer)
        embed = disnake.Embed(
            title=self.title.format(id=report.id),
            description=description,
            color=disnake.Color.yellow()
        )

        if inter.channel.type == disnake.ChannelType.private:
            author = "Anonym"
        else:
            author = f"{inter.author.mention} @{inter.author.name}"

        embed.add_field(name="Answered by", value=author, inline=False)
        utils.add_author_footer(embed, inter.author, additional_text=[f"ID: {report.id}"])
        return embed

    async def callback(self, inter: disnake.ModalInteraction) -> None:
        answer = inter.text_values['answer']
        report = Report.get_report(self.report_id)
        report_author = await self.bot.get_or_fetch_user(report.author_id)
        report_message = await report_features.convert_url(inter, report.report_url)
        embed = self.answer_embed(inter, report, answer)
        Answer.add_answer(self.report_id, inter.author.id, answer)

        # interaction in DMs
        if inter.channel.type == disnake.ChannelType.private:
            await report_message.thread.send(embed=embed, view=ReportAnswerOnlyView(self.bot))
            await inter.response.edit_message(view=None)
        # interaction in thread
        elif inter.channel.type == disnake.ChannelType.public_thread:
            await report_message.thread.send(embed=embed)
            await inter.response.edit_message(view=None)
        # interaction in channel
        else:
            await report_message.thread.send(embed=embed)

        await report_author.send(embed=embed, view=ReportAnonymView(self.bot))
        await inter.send(Messages.report_modal_success, ephemeral=True)
