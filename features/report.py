import re
from typing import Optional

import disnake
from disnake.ext import commands


def extract_report_id(inter: disnake.MessageInteraction) -> int:
    """extracts the report id from the footer of the report embed"""
    report_id = re.match(r".+ \| ID: (\d+).*", inter.message.embeds[0].footer.text).group(1)
    return int(report_id)


async def convert_url(inter, message_url) -> Optional[disnake.Message]:
    """converts a message url to a message object"""
    try:
        message: disnake.Message = await commands.MessageConverter().convert(inter, message_url)
    except commands.MessageNotFound:
        message = None
    return message


async def embed_resolved(
    self,
    author: str,
    embed: dict,
    report_type: str,
    resolved: bool
) -> disnake.Embed:
    if resolved:
        embed["color"] = disnake.Color.green()
        embed["title"] = "Resolved"
        for field in embed["fields"]:
            if field["name"] == "Resolved by":
                field["value"] = author
        for child in self.children:
            child.disabled = True
            if child.custom_id == "report:resolve":
                child.label = "Resolved"
                child.style = disnake.ButtonStyle.green
                child.emoji = "✅"
                child.disabled = False
    else:
        embed["color"] = disnake.Color.red()
        embed["title"] = f"{report_type.capitalize()} report"
        for field in embed["fields"]:
            if field["name"] == "Resolved by":
                field["value"] = "---"
        for child in self.children:
            child.disabled = False
            if child.custom_id == "report:resolve":
                child.label = "Resolve"
                child.style = disnake.ButtonStyle.grey
                child.emoji = "❌"
    embed = disnake.Embed.from_dict(embed)
    return embed
