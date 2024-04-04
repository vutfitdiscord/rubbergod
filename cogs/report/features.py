import re
from datetime import datetime, timezone

import disnake
from disnake.ext import commands

import utils
from database.report import ReportDB

from .features_errors import ButtonInteractionError
from .messages_cz import MessagesCZ


def extract_report_id(inter: disnake.MessageInteraction) -> int:
    """extracts the report id from the footer of the report embed"""
    if not inter.message.embeds:
        raise ButtonInteractionError(inter.author.mention, MessagesCZ.missing_embed)

    report_id = re.match(r".+ \| ID: (\d+).*", inter.message.embeds[0].footer.text)
    if not report_id:
        raise ButtonInteractionError(inter.author.mention, MessagesCZ.report_id_missing)
    return int(report_id.group(1))


async def convert_url(inter: disnake.ApplicationCommandInteraction, message_url: str) -> disnake.Message:
    """converts a message url to a message object"""
    try:
        message: disnake.Message = await commands.MessageConverter().convert(inter, message_url)
    except commands.MessageNotFound:
        raise ButtonInteractionError(inter.author.mention, MessagesCZ.report_not_found)
    return message


async def set_tag(forum: disnake.ForumChannel, forum_thread: disnake.Thread, tag_name: str) -> None:
    """Remove all tags and add the tag with the given name"""
    for tag in forum.available_tags:
        if tag.name.lower() == tag_name:
            await forum_thread.edit(applied_tags=[tag])
            break


async def embed_resolved(
    buttons: list[disnake.ui.Button], author: str, embed: dict, report_type: str, resolved: bool
) -> disnake.Embed:
    """Changes the embed to a resolved embed or back to a report embed"""
    if resolved:
        embed["color"] = disnake.Color.green()
        embed["title"] = "Resolved"
        for field in embed["fields"]:
            if field["name"] == "Resolved by":
                field["value"] = author
        for button in buttons:
            button.disabled = True
            if button.custom_id == "report:resolve":
                button.label = "Resolved"
                button.style = disnake.ButtonStyle.green
                button.emoji = "✅"
                button.disabled = False
    else:
        embed["color"] = disnake.Color.red()
        embed["title"] = f"{report_type.capitalize()} report"
        for field in embed["fields"]:
            if field["name"] == "Resolved by":
                field["value"] = "---"
        for button in buttons:
            button.disabled = False
            if button.custom_id == "report:resolve":
                button.label = "Resolve"
                button.style = disnake.ButtonStyle.grey
                button.emoji = "❌"
    embed = disnake.Embed.from_dict(embed)
    return embed


def answer_embed(title: str, inter: disnake.ModalInteraction, report: ReportDB, answer: str) -> disnake.Embed:
    """creates an embed template for the submitted answer"""
    description = MessagesCZ.embed_answered(last_answer=report.last_answer, answer=answer)
    embed = disnake.Embed(title=title, description=description, color=disnake.Color.yellow())

    if inter.channel.type == disnake.ChannelType.private:
        author = "Anonym"
        embed.timestamp = datetime.now(tz=timezone.utc)
        embed.set_footer(icon_url=inter.author.default_avatar.url, text=f"{author} | ID: {report.id}")

    else:
        author = f"{inter.author.mention} `@{inter.author.name}`"
        utils.add_author_footer(embed, inter.author, additional_text=[f"ID: {report.id}"])

    embed.add_field(name="Answered by", value=author, inline=False)
    return embed


def info_message_embed(
    inter: disnake.ModalInteraction, report: ReportDB, title: str, description: str
) -> disnake.Embed:
    """creates info embed for the report"""
    embed = disnake.Embed(title=title, description=description, color=disnake.Color.yellow())

    utils.add_author_footer(embed, inter.author, additional_text=[f"ID: {report.id}"])
    return embed
