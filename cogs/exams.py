"""
Cog to parse exams data from website and send it to channel.
Available for each year of study.
"""

import collections
import datetime
import math
import re
from typing import List, Optional, Union

import disnake
import requests
from bs4 import BeautifulSoup
from bs4.element import NavigableString
from disnake.ext import commands, tasks

import utils
from buttons.embed import EmbedView
from cogs.base import Base
from config import cooldowns
from config.messages import Messages
from database.exams import ExamsTermsMessageDB
from permissions import permission_check

year_regex = "[1-3][BM]IT"
YEAR_LIST = ["1BIT", "2BIT", "3BIT", "1MIT", "2MIT"]
CLEANR = re.compile("<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});")

DATE_OFFSET = 14
TIME_OFFSET = 14


class Exams(Base, commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

        self.subscribed_guilds: List[int] = []
        if self.config.exams_subscribe_default_guild:
            self.subscribed_guilds.append(self.config.guild_id)

        if self.subscribed_guilds:
            self.tasks = [self.update_terms_task.start()]

    @cooldowns.default_cooldown
    @commands.check(permission_check.helper_plus)
    @commands.slash_command(name="terms")
    async def terms(self, inter: disnake.ApplicationCommandInteraction):
        """Group of commands for terms."""
        await inter.response.defer()

    @terms.sub_command(name="update", description=Messages.exams_update_term_brief)
    async def update(self, inter: disnake.ApplicationCommandInteraction):
        updated_chans = await self.update_exam_terms(inter.guild, inter.author)
        await inter.edit_original_response(Messages.exams_terms_updated(num_chan=updated_chans))

    @commands.check(permission_check.mod_plus)
    @terms.sub_command(name="remove_all", description=Messages.exams_remove_all_terms_brief)
    async def remove_all(self, inter: disnake.ApplicationCommandInteraction):
        for channel in inter.guild.channels:
            if not isinstance(channel, disnake.TextChannel):
                continue

            for channel_name in self.config.exams_term_channels:
                if channel_name.lower() == channel.name.lower():
                    message_ids = ExamsTermsMessageDB.remove_from_channel(channel.id)
                    for message_id in message_ids:
                        try:
                            message = await channel.fetch_message(message_id)
                            await message.delete()
                        except disnake.NotFound:
                            pass
        await inter.edit_original_response(Messages.exams_terms_removed)

    @commands.check(permission_check.mod_plus)
    @terms.sub_command(name="remove", description=Messages.exams_remove_terms_brief)
    async def remove(self, inter: disnake.ApplicationCommandInteraction, channel: disnake.TextChannel):
        if not isinstance(channel, disnake.TextChannel):
            await inter.edit_original_response(
                Messages.exams_channel_is_not_text_channel(chan_name=channel.name)
            )
            return

        message_ids = ExamsTermsMessageDB.remove_from_channel(channel.id)
        for message_id in message_ids:
            try:
                message = await channel.fetch_message(message_id)
                await message.delete()
            except disnake.NotFound:
                pass

        if message_ids:
            await inter.send(Messages.exams_terms_removed)
        else:
            await inter.send(Messages.exams_nothing_to_remove(chan_name=channel.name))

    @commands.check(permission_check.mod_plus)
    @terms.sub_command(name="start", description=Messages.exams_start_terms_brief)
    async def start(self, inter: disnake.ApplicationCommandInteraction):
        if inter.guild.id not in self.subscribed_guilds:
            self.subscribed_guilds.append(inter.guild.id)

        if not self.update_terms_task.is_running():
            self.update_terms_task.start()
        else:
            # If task is already running update terms now
            await self.update_exam_terms(inter.guild)

        await inter.send(Messages.exams_automatic_update_started(guild_name=inter.guild.name))

    @commands.check(permission_check.mod_plus)
    @terms.sub_command(name="stop", description=Messages.exams_stop_terms_brief)
    async def stop(self, inter: disnake.ApplicationCommandInteraction):
        if inter.guild in self.subscribed_guilds:
            self.subscribed_guilds.remove(inter.guild.id)

        # If there are no subscribed guilds terminate whole task
        if not self.subscribed_guilds:
            self.update_terms_task.cancel()

        await inter.send(Messages.exams_automatic_update_stopped(guild_name=inter.guild.name))

    @tasks.loop(hours=int(Base.config.exams_terms_update_interval * 24))
    async def update_terms_task(self):
        for guild in self.subscribed_guilds:
            guild = disnake.utils.get(self.bot.guilds, id=guild)
            if guild is not None:
                await self.update_exam_terms(guild)

    @staticmethod
    def process_match(match):
        year = match.string[match.regs[0][0]: match.regs[0][1]]
        return year

    @staticmethod
    def list_int(input) -> List[int]:
        """Convert any list to list of integers"""
        return list(map(int, input))

    async def get_message_destination(self, channel: disnake.TextChannel, message_index: int = 0):
        saved_messages = ExamsTermsMessageDB.get_message_from_channel(channel.id)
        if saved_messages and message_index < len(saved_messages):
            if message_index < 0:
                message_index = 0
            message_id = int(saved_messages[message_index].message_id)

            dest = None
            try:
                dest = await channel.fetch_message(message_id)
            except disnake.NotFound:
                # If cant find message then remove it from database
                ExamsTermsMessageDB.remove_term_message(message_id)

            # If message is not found then set it to channel itself
            if dest is None:
                dest = channel
        else:
            dest = channel

        return dest

    async def update_exam_terms(self, guild: disnake.Guild, author: Optional[disnake.User] = None):
        updated = 0

        for channel in guild.channels:
            if not isinstance(channel, disnake.TextChannel):
                continue

            for channel_name in self.config.exams_term_channels:
                if channel_name.lower() == channel.name.lower():
                    if not channel_name[0].isdigit():
                        if channel_name[:3].upper() == "MIT":
                            dest1 = await self.get_message_destination(channel, 0)
                            dest2 = await self.get_message_destination(channel, 1)

                            await self.process_exams(dest1, "1MIT", author)
                            await self.process_exams(dest2, "2MIT", author)
                            updated += 1
                    else:
                        match = re.match(year_regex, channel_name[:4].upper())
                        if match is not None:
                            year = self.process_match(match)
                            if year is not None:
                                dest = await self.get_message_destination(channel)

                                await self.process_exams(dest, year, author)
                                updated += 1

        return updated

    @commands.slash_command(name="exams", description=Messages.exams_brief, aliases=["zkousky"])
    async def exams(
        self,
        inter: disnake.ApplicationCommandInteraction,
        rocnik: str = commands.Param(name='rocnik', choices=YEAR_LIST, default=None)
    ):
        await inter.response.defer()
        if rocnik is None:
            if isinstance(inter.author, disnake.Member):
                user_roles: List[disnake.Role] = inter.author.roles

                for role in user_roles:
                    match = re.match(year_regex, role.name.upper())

                    if match is not None:
                        rocnik = self.process_match(match)
                        if rocnik is not None:
                            await self.process_exams(inter, rocnik, inter.author)
                            return

                await inter.edit_original_response(Messages.exams_no_valid_role)
            else:
                await inter.edit_original_response(Messages.exams_specify_year)
        else:
            await self.process_exams(inter, rocnik, inter.author)

    async def process_exams(
        self,
        target: Union[disnake.ApplicationCommandInteraction, disnake.TextChannel, disnake.Message],
        year: Union[str, None],
        author: Optional[disnake.User] = None,
    ):
        """
        Get exams data from web, parse and send/update message

        params:
            target:
                Intercation: called from `exam` command
                TextChannel: called on `term` start command
                Message: called on `term` update cron job
            year: one of `YEAR_LIST` or None, get just specified year info
            author: author of command to display in embed footer
        """
        date = datetime.date.today()

        semester = "ZS"
        if 3 < date.month < 9:
            semester = "LS"

        cal_year = date.year
        if date.month < 9:
            cal_year -= 1

        all_url = f"https://minerva3.fit.vutbr.cz/rozvrhis/{semester}{cal_year}/zkousky"
        year_url = f"{all_url}/{year}"
        description = f"[Odkaz na zkoušky ročníku]({year_url})\n" if year else ""
        description += f"[Odkaz na všechny zkoušky]({all_url})"

        title = (
            f"Zkoušky {year} {semester}{cal_year}-{cal_year + 1}"
            if year
            else f"Zkoušky {semester}{cal_year}-{cal_year + 1}"
        )

        r = requests.get(year_url)
        if r.status_code != 200:
            # Site returned fail code
            embed = disnake.Embed(title=title, description=description, color=disnake.Color.dark_blue())
            utils.add_author_footer(embed, author if author is not None else self.bot.user)
            if isinstance(target, disnake.ApplicationCommandInteraction):
                await target.send(embed=embed)
            return

        soup = BeautifulSoup(r.content, "html.parser")

        table = soup.find("table", {"class": "exam"})
        body = table.find("tbody")

        if body is None:
            # There is no table so no terms
            embed = disnake.Embed(title=title, description=description, color=disnake.Color.dark_blue())
            utils.add_author_footer(embed, author if author is not None else self.bot.user)

            if isinstance(target, disnake.ApplicationCommandInteraction):
                await target.send(embed=embed)
                return

        # There is body so start parsing table
        exams = body.find_all("tr")

        number_of_exams = len(exams)
        bs = self.config.exams_page_size
        number_of_batches = math.ceil(number_of_exams / bs)
        exam_batches = [exams[i * bs: bs + i * bs] for i in range(number_of_batches)]

        term_strings_dict = {}
        pages = []
        for exam_batch in exam_batches:
            embed = disnake.Embed(title=title, description=description, color=disnake.Color.dark_blue())
            utils.add_author_footer(embed, author if author is not None else self.bot.user)

            for exam in exam_batch:
                # Every exams row start with link tag
                tag = exam.find("a") if str(exam).startswith("<tr><td><a") else None
                cols = exam.find_all("td")

                # Check if tag is not None and get strong and normal subject tag
                subject_tag = (tag.find("strong") or tag.contents[0]) if tag is not None else None

                if subject_tag is None:
                    content = re.sub(CLEANR, "", str(cols[0]))
                    embed.add_field(name="Poznámka", value=content, inline=False)
                else:
                    del cols[0]

                    if not isinstance(subject_tag, NavigableString):
                        subject_tag = subject_tag.contents[0]

                    col_count = len(cols)
                    if col_count == 1:
                        # Support for credits
                        col = cols[0]
                        strong_tag = col.find("strong")

                        if strong_tag is None:
                            # There is no term - Only text
                            embed.add_field(name=subject_tag, value=col.contents[0], inline=False)
                        else:
                            # Mainly for terms without specified time
                            term_date_str = strong_tag.contents[0].replace("\xa0", "").replace(" ", "")

                            date_splits = self.list_int(term_date_str.split("."))
                            date_splits.reverse()  # from DDMMYYYY to YYYYMMDD
                            # Without actual time set time to end of the day
                            term_datetime = datetime.datetime(*date_splits, 23, 59)

                            term_date = datetime.date(*date_splits)

                            term_content = f"{term_date_str}\n{col.contents[0]}"

                            # Calculate character offsets
                            padded_term_date = datetime.date.strftime(term_date, "%d.%m.%Y")
                            date_offset = " " * (DATE_OFFSET - len(subject_tag))
                            time_offset = " " * (
                                TIME_OFFSET - len(padded_term_date)
                            )  # Here used aas data offset
                            term_string = f"{subject_tag}{date_offset}{padded_term_date}"
                            term_string += f"{time_offset}{col.contents[0]}"

                            if term_date == datetime.date.today():
                                term_strings_dict[term_datetime] = f"- {term_string}"
                            elif term_datetime < datetime.datetime.now():
                                subject_tag = f"~~{subject_tag}~~"
                                term_content = f"~~{term_content}~~"
                            else:
                                term_strings_dict[term_datetime] = f"+ {term_string}"

                            embed.add_field(name=subject_tag, value=term_content, inline=False)
                    else:
                        # Classic terms
                        whole_term_count = 0
                        for idx, col in enumerate(cols):
                            terms = col.find_all("strong")
                            times = col.find_all("em")

                            number_of_terms = len(terms)
                            whole_term_count += number_of_terms

                            for idx2, (term_date_str, time) in enumerate(zip(terms, times)):
                                term_date_str = (
                                    term_date_str.contents[0].replace("\xa0", "").replace(" ", "")
                                )
                                term_time_str = ""
                                for c in time.contents:
                                    term_time_str += str(c)
                                term_time_str = term_time_str.replace("<sup>", ":").replace("</sup>", "")

                                date_splits = self.list_int(term_date_str.split("."))
                                date_splits.reverse()  # from DDMMYYYY to YYYYMMDD

                                start_time_str_parts = self.list_int(
                                    term_time_str.split("-")[0].replace(" ", "").split(":")
                                )
                                end_time_str_parts = self.list_int(
                                    term_time_str.split("-")[1].replace(" ", "").split(":")
                                )

                                term_datetime = datetime.datetime(
                                    *date_splits,
                                    *start_time_str_parts,
                                )

                                term_date = datetime.date(*date_splits)

                                if (
                                    start_time_str_parts is not None
                                    and end_time_str_parts is not None
                                ):

                                    start_time = datetime.time(*start_time_str_parts)
                                    start_time_str = datetime.time.strftime(start_time, "%H:%M")
                                    end_time = datetime.time(*end_time_str_parts)
                                    end_time_str = datetime.time.strftime(end_time, "%H:%M")
                                    term_time_str = f"{start_time_str} - {end_time_str}"

                                padded_term_date = datetime.date.strftime(term_date, "%d.%m.%Y")
                                term_date_time_string = f"{padded_term_date} {term_time_str}"

                                name = (
                                    f"{idx + 1}.  {subject_tag}"
                                    if number_of_terms == 1
                                    else f"{idx + 1}.{idx2 + 1} {subject_tag}"
                                )

                                # Calculate character offsets
                                date_offset = " " * (DATE_OFFSET - len(name))
                                time_offset = " " * (TIME_OFFSET - len(padded_term_date))
                                term_string = f"{name}{date_offset}{padded_term_date}"
                                term_string += f"{time_offset}{term_time_str}"

                                if term_date == datetime.date.today():
                                    term_strings_dict[term_datetime] = f"- {term_string}"
                                elif term_datetime < datetime.datetime.now():
                                    name = f"~~{name}~~"
                                    term_date_time_string = f"~~{term_date_time_string}~~"
                                else:
                                    term_strings_dict[term_datetime] = f"+ {term_string}"

                                embed.add_field(name=name, value=term_date_time_string)

                        to_add = math.ceil(whole_term_count / 3) * 3 - whole_term_count
                        for _ in range(to_add):
                            embed.add_field(name="\u200b", value="\u200b")

            pages.append(embed)

        if len(pages) == 0:
            embed = disnake.Embed(title=title, description=description, color=disnake.Color.dark_blue())
            utils.add_author_footer(embed, author if author is not None else self.bot.user)
            pages.append(embed)
        if isinstance(target, disnake.ApplicationCommandInteraction):
            view = EmbedView(target.author, pages)
            view.message = await target.edit_original_response(embed=pages[0], view=view)
        else:
            header = disnake.Embed(
                title=title, description=description, color=disnake.Color.dark_blue()
            )
            await self.handle_exams_with_database_access(term_strings_dict, header, target)

    async def handle_exams_with_database_access(
        self, src_data: dict, header: disnake.Embed, dest: Union[disnake.TextChannel, disnake.Message]
    ):
        sorted_src_data = collections.OrderedDict(sorted(src_data.items()))

        too_much_terms = False

        if sorted_src_data:
            dates = list(sorted_src_data.keys())
            first_date = dates[0]
            last_week_number = first_date.isocalendar()[1]

            data_by_weeks = []
            current_week_data = []
            for date in dates:
                term_string = sorted_src_data.get(date)
                current_week_number = date.isocalendar()[1]
                if last_week_number != current_week_number:
                    last_week_number = current_week_number
                    data_by_weeks.append("\n".join(current_week_data))
                    current_week_data.clear()
                current_week_data.append(term_string)

            if current_week_data:
                data_by_weeks.append("\n".join(current_week_data))

            src_data_string = ""
            for week_string in data_by_weeks:
                if (len(src_data_string) + len(week_string) + 2) > 1900:
                    too_much_terms = True
                    break

                if src_data_string:
                    src_data_string = f"{src_data_string}\n\n{week_string}"
                else:
                    src_data_string = week_string

        else:
            src_data_string = None

        if src_data_string is not None:
            if too_much_terms:
                src_data_string = f"{src_data_string}\n\nZbytek termínů v odkazu"
            src_data_string = f"```diff\n{src_data_string}\n```"

        if isinstance(dest, disnake.TextChannel):
            # No previous message in channel
            send_message = await dest.send(content=src_data_string, embed=header)
            if send_message is not None:
                ExamsTermsMessageDB.create_term_message(send_message.id, send_message.channel.id)
        else:
            # Message already exists
            await dest.edit(content=src_data_string, embed=header)


def setup(bot):
    bot.add_cog(Exams(bot))
