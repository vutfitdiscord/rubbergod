import re
from datetime import datetime, timezone
from typing import Optional

import disnake
from disnake.ext import commands

import utils
from config.messages import Messages
from database.report import ReportDB


def extract_report_id(inter: disnake.MessageInteraction) -> int:
    """extracts the report id from the footer of the report embed"""
    report_id = re.match(r'.+ \| ID: (\d+).*', inter.message.embeds[0].footer.text).group(1)
    return int(report_id)


async def convert_url(inter, message_url) -> Optional[disnake.Message]:
    """converts a message url to a message object"""
    try:
        message: disnake.Message = await commands.MessageConverter().convert(inter, message_url)
    except commands.MessageNotFound:
        message = None
    return message


async def set_tag(forum: disnake.ForumChannel, forum_thread: disnake.Thread, tag_name: str) -> None:
    """Remove all tags and add the tag with the given name"""
    for tag in forum.available_tags:
        if tag.name.lower() == tag_name:
            await forum_thread.edit(applied_tags=[tag])
            break


async def embed_resolved(
    self,
    author: str,
    embed: dict,
    report_type: str,
    resolved: bool
) -> disnake.Embed:
    """Changes the embed to a resolved embed or back to a report embed"""
    if resolved:
        embed['color'] = disnake.Color.green()
        embed['title'] = 'Resolved'
        for field in embed['fields']:
            if field['name'] == 'Resolved by':
                field['value'] = author
        for child in self.children:
            child.disabled = True
            if child.custom_id == 'report:resolve':
                child.label = 'Resolved'
                child.style = disnake.ButtonStyle.green
                child.emoji = '✅'
                child.disabled = False
    else:
        embed['color'] = disnake.Color.red()
        embed['title'] = f'{report_type.capitalize()} report'
        for field in embed['fields']:
            if field['name'] == 'Resolved by':
                field['value'] = '---'
        for child in self.children:
            child.disabled = False
            if child.custom_id == 'report:resolve':
                child.label = 'Resolve'
                child.style = disnake.ButtonStyle.grey
                child.emoji = '❌'
    embed = disnake.Embed.from_dict(embed)
    return embed


def answer_embed(title, inter: disnake.ModalInteraction, report: ReportDB, answer: str) -> disnake.Embed:
    """creates an embed template for the submitted answer"""
    description = Messages.report_embed_answered(last_answer=report.last_answer, answer=answer)
    embed = disnake.Embed(
        title=title,
        description=description,
        color=disnake.Color.yellow()
    )

    if inter.channel.type == disnake.ChannelType.private:
        author = 'Anonym'
        embed.timestamp = datetime.now(tz=timezone.utc)
        embed.set_footer(
            icon_url=inter.author.default_avatar.url,
            text=f'{author} | ID: {report.id}'
        )

    else:
        author = f'{inter.author.mention} @{inter.author.display_name}'
        utils.add_author_footer(embed, inter.author, additional_text=[f'ID: {report.id}'])

    embed.add_field(name='Answered by', value=author, inline=False)
    return embed


def deleted_message_embed(
    inter: disnake.ModalInteraction,
    report: ReportDB,
    description: str
) -> disnake.Embed:
    """creates an embed template for the submitted answer"""
    embed = disnake.Embed(
        title=Messages.report_message_deleted_title(id=report.id),
        description=description,
        color=disnake.Color.yellow()
    )

    utils.add_author_footer(embed, inter.author, additional_text=[f'ID: {report.id}'])
    return embed
