"""Helper functions for message logging."""

import disnake

import utils


async def create_message_log_embed(
    title: str,
    color: disnake.Color,
    channel: disnake.TextChannel,
    message_link: str,
    content_preview: str = None,
    attachments_count: int = None,
    author: disnake.User = None,
    additional_fields: list[tuple[str, str]] = None,
) -> disnake.Embed:
    """Create a standardized embed for message logging.

    Args:
        title: The embed title (e.g., "📤 Message sent")
        color: The embed color
        channel: The channel where the message was sent/edited
        message_link: Jump URL to the message
        content_preview: Optional preview of the message content
        attachments_count: Optional number of attachments
        author: The user who performed the action
        additional_fields: Optional list of (name, value) tuples for extra fields

    Returns:
        A configured disnake.Embed ready to send to log channel
    """
    embed = disnake.Embed(title=title, color=color)
    embed.add_field(name="Channel", value=channel.mention, inline=False)
    embed.add_field(name="Message link", value=f"[Jump to message]({message_link})", inline=False)

    if additional_fields:
        for field_name, field_value in additional_fields:
            embed.add_field(name=field_name, value=field_value, inline=False)

    if content_preview:
        embed.add_field(name="Content preview", value=content_preview, inline=False)

    if attachments_count:
        embed.add_field(name="Attachments", value=f"{attachments_count} file(s)", inline=False)

    if author:
        utils.embed.add_author_footer(embed, author)

    return embed
