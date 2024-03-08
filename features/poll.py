import re
from datetime import datetime, timedelta
from typing import List, Union

import disnake
from disnake.ext import commands

import utils
from config.messages import Messages
from database.poll import PollDB


def extract_poll_id(message: disnake.Message) -> int:
    """extracts the report id from the footer of the report embed"""
    poll_id = re.match(r".+ \| ID: (\d+).*", message.embeds[0].footer.text).group(1)
    return int(poll_id)


async def check_end(
    inter: disnake.ApplicationCommandInteraction,
    end: str
) -> tuple[bool, datetime]:
    """Check if end is valid and above 5min from now"""
    end: datetime = utils.parse_time(end, Messages.time_format)
    now = inter.created_at + timedelta(minutes=5)

    if (end - now) > timedelta(days=365):
        await inter.send(Messages.poll_end_long, ephemeral=True)
        return False, end
    elif end < now:
        await inter.send(Messages.poll_end_short, ephemeral=True)
        return False, end
    return True, end


async def parse_attachment(attachment: disnake.Attachment) -> Union[str, disnake.File, None]:
    """parses the attachment url to get the attachment as file"""
    if attachment is None or attachment.content_type is None:
        return None, None
    if "image" in attachment.content_type:
        return "image", await attachment.to_file()
    else:
        return "file", await attachment.to_file()


def update_embed(embed: disnake.Embed, poll: PollDB) -> disnake.Embed:
    """update the embed with new votes"""
    embed.clear_fields()
    all_votes = poll.get_voters_count()
    for option in poll.options:
        votes = len(option.voters)
        embed.add_field(
            name=f"{option.emoji} {option.text}",
            value=f"{utils.create_bar(votes, all_votes)} ({votes} hlasů)",
            inline=True
        )

    pattern = r"- Celkový počet hlasů: (\d+)"
    embed.description = re.sub(pattern, f"- Celkový počet hlasů: {all_votes}", embed.description)

    return embed


def close_embed(embed: disnake.Embed, poll: PollDB, user_id: str, now: datetime) -> disnake.Embed:
    """update the embed as closed poll with new timestamp"""
    mention = utils.generate_mention(user_id)
    pattern = re.compile(r'Konec: <t:(\d+):R>')
    timestamp = int(now.timestamp())
    updated_description = pattern.sub(f'Konec: <t:{timestamp}:R>', embed.description)
    embed.description = updated_description

    embed = update_embed(embed, poll)

    embed.add_field(
        name="Ukončeno předčasně",
        value=f"{mention} ukončil hlasování předčasně.",
        inline=False
    )

    return embed


def create_embed(
    title: str,
    description: str,
    author: Union[disnake.User, disnake.Member],
    end: datetime,
    poll_id: int,
    poll_options: list = [],
    max_votes: int = 1,
    image: disnake.File = None,
    anonymous: bool = False,
    **kwargs
) -> disnake.Embed:
    """Embed template for Poll"""
    end = utils.get_discord_timestamp(end, style="Relative Time")
    description = Messages.poll_embed_description(
        description=description,
        votes=max_votes,
        date=end,
        anonymous=anonymous,
        all_votes=0,
    )
    embed = disnake.Embed(
        title=title,
        description=description,
        color=disnake.Color.blue(),
    )
    for emoji, option in poll_options.items():
        embed.add_field(
            name=f"{emoji} {option}",
            value=f"{utils.create_bar(0, 0)} ({0} hlasů)",
            inline=True
        )
    if image:
        embed.set_image(file=image)
    utils.add_author_footer(embed, author, additional_text=[f"ID: {poll_id}"])
    return embed


async def list_voters(inter: disnake.ApplicationCommandInteraction) -> List[str]:
    poll = PollDB.get(extract_poll_id(inter.message))

    if poll is None:
        await inter.send(Messages.poll_not_found)
        return

    if poll.anonymous:
        await inter.send(Messages.poll_is_anonymous)
        return

    voters = poll.get_voters()
    if not voters:
        await inter.send(Messages.poll_no_voters)
        return

    content = f"# [{poll.title}]({poll.message_url})\n"
    for poll_option, voters in voters.items():
        content += f"### **{poll_option.emoji} {poll_option.text}**\n"
        for index, voter in enumerate(voters):
            voter = utils.generate_mention(voter)
            content += f"{voter} "
            if (index+1) % 5 == 0 and index != 0 or index == len(voters) - 1:
                # only 5 mentions per line
                content += "\n"

    content = utils.cut_string_by_words(content, 1900, "\n")
    return content


def create_end_poll_message(poll: PollDB) -> str:
    winning_options = poll.get_winning_options()
    total_votes = poll.get_voters_count()
    content = Messages.poll_closed(title=poll.title, url=poll.message_url)

    if total_votes <= 0:
        return content

    if len(winning_options) > 1:
        options = "".join([f"\n{option.emoji} {option.text}" for option in winning_options])
        content += Messages.poll_tie_options(
            options=options,
            votes=winning_options[0].voters_count,
            percentage=round(winning_options[0].voters_count / total_votes * 100),
        )
    else:
        winning_option = winning_options[0]
        content += Messages.poll_winning_option(
            option=f"{winning_option.emoji} {winning_option.text}",
            votes=winning_option.voters_count,
            percentage=round(winning_option.voters_count / total_votes * 100),
        )
    return content


async def has_cooldown(
    inter: disnake.ApplicationCommandInteraction,
    button_cd: commands.CooldownMapping
) -> bool:
    bucket = button_cd.get_bucket(inter)
    retries = bucket.get_tokens()
    retry = bucket.update_rate_limit()
    if retries == 1:
        time = datetime.now() + timedelta(seconds=bucket.get_retry_after())
        timestamp = utils.get_discord_timestamp(time, style="Relative Time")
        await inter.send(Messages.poll_button_spam(time=timestamp), ephemeral=True)
        return True

    if retry:
        return True

    return False
