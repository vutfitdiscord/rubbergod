import disnake
from disnake.ext import commands, tasks
import datetime
from typing import Union, List, Optional
import re
import requests
from bs4 import BeautifulSoup
from bs4.element import NavigableString
import math
import collections

from repository.exams_repo import ExamsTermsMessageRepo
from features.paginator import PaginatorSession
from config.app_config import config
from config import cooldowns
from config.messages import Messages
import utils
from features.list_message_sender import merge_messages

year_regex = "[1-4][BM]IT"
CLEANR = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')

DATE_OFFSET = 14
TIME_OFFSET = 14

class Exams(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot

        self.subscribed_guilds:List[int] = []
        self.exams_repo = ExamsTermsMessageRepo()

    def cog_unload(self):
        if self.update_terms_task.is_running():
            self.update_terms_task.cancel()
        self.subscribed_guilds = []

    def __del__(self):
        if self.update_terms_task.is_running():
            self.update_terms_task.cancel()

    @cooldowns.default_cooldown
    @commands.check(utils.helper_plus)
    @commands.command()
    async def update_terminy(self, ctx:commands.Context):
        await self.update_exam_terms(ctx.guild, ctx.author)
        await ctx.send("`Termíny aktualizovány`")

    @commands.check(utils.is_bot_admin)
    @commands.command()
    async def start_terminy(self, ctx: commands.Context):
        self.subscribed_guilds.append(ctx.guild.id)

        if not self.update_terms_task.is_running():
            self.update_terms_task.start()
        else:
            # If task is already running update terms now
            await self.update_exam_terms(ctx.guild)

        await ctx.send(f"`Zapnuta automatická aktualizace termínů pro server: {ctx.guild.name}`")

    @commands.check(utils.is_bot_admin)
    @commands.command()
    async def stop_terminy(self, ctx: commands.Context):
        if ctx.guild in self.subscribed_guilds:
            self.subscribed_guilds.remove(ctx.guild.id)

        # If there are no subscribed guilds terminate whole task
        if not self.subscribed_guilds:
            self.update_terms_task.cancel()

        await ctx.send(f"`Zastavena automatická aktualizace termínů pro server: {ctx.guild.name}`")

    @tasks.loop(hours=int(config.exams_terms_update_interval * 24))
    async def update_terms_task(self):
        for guild in self.subscribed_guilds:
            guild = disnake.utils.get(self.bot.guilds, id=guild)
            if guild is not None:
                await self.update_exam_terms(guild)

    @staticmethod
    def process_match(match):
        year = match.string[match.regs[0][0]: match.regs[0][1]]
        if year in ("4BIT", "3MIT"):
            year = str(int(year[0]) - 1) + year[1:]

        if year == "4MIT":
            return None
        return year

    async def get_message_destination(self, channel:disnake.TextChannel, message_index:int=0):
        saved_messages = self.exams_repo.get_message_from_channel(channel.id)
        if saved_messages and message_index < len(saved_messages):
            if message_index < 0:
                message_index = 0
            message_id = int(saved_messages[message_index].message_id)

            dest = None
            try:
                dest = await channel.fetch_message(message_id)
            except:
                # If cant find message then remove it from database
                self.exams_repo.remove_term_message(message_id)

            # If message is not found then set it to channel itself
            if dest is None: dest = channel
        else:
            dest = channel

        return dest

    async def update_exam_terms(self, guild:disnake.Guild, author:Optional[disnake.User]=None):
        for channel_name in config.exams_term_channels:
            for channel in guild.channels:
                if not isinstance(channel, disnake.TextChannel):
                    continue

                if channel_name.lower() == channel.name.lower():
                    if not channel_name[0].isdigit():
                        if channel_name[:3].lower() == "mit":
                            dest1 = await self.get_message_destination(channel, 0)
                            dest2 = await self.get_message_destination(channel, 1)

                            await self.process_exams(dest1, "1MIT", author)
                            await self.process_exams(dest2, "2MIT", author)
                    else:
                        match = re.match(year_regex, channel_name[:4].upper())
                        if match is not None:
                            year = self.process_match(match)
                            if year is not None:
                                dest = await self.get_message_destination(channel)

                                await self.process_exams(dest, year, author)

    @commands.command(brief=Messages.exams_brief, aliases=["zkousky"])
    async def exams(self, ctx:commands.Context, rocnik:Union[str, None]=None):
        if rocnik is None:
            if isinstance(ctx.author, disnake.Member):
                user_roles: List[disnake.Role] = ctx.author.roles

                for role in user_roles:
                    match = re.match(year_regex, role.name.upper())

                    if match is not None:
                        rocnik = self.process_match(match)
                        if rocnik is None:
                            return await ctx.send(Messages.exams_no_valid_year)
                        return await self.process_exams(ctx, rocnik, ctx.author)

                await ctx.send(Messages.exams_no_valid_role)
            else:
                try:
                    await ctx.send(Messages.exams_specify_year)
                except:
                    pass
        else:
            match = re.match(year_regex, rocnik.upper())

            if match is not None:
                rocnik = self.process_match(match)
                if rocnik is None:
                    return await ctx.send(Messages.exams_no_valid_year)
                await self.process_exams(ctx, rocnik, ctx.author)
            else:
                await ctx.send(Messages.exams_no_valid_year)

    async def process_exams(self, ctx:Union[commands.Context, disnake.TextChannel, disnake.Message],
                            year:Union[str, None],
                            author:Optional[disnake.User]=None):
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

        title = f"Zkoušky {year} {semester}{cal_year}-{cal_year + 1}" \
            if year else f"Zkoušky {semester}{cal_year}-{cal_year + 1}"

        r = requests.get(year_url)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'html.parser')

            try:
                table = soup.find("table", {"class": "exam"})
                body = table.find("tbody")

                if body is None:
                    # There is no table so no terms
                    embed = disnake.Embed(title=title, description=description,
                                          color=disnake.Color.dark_blue())
                    utils.add_author_footer(embed, author if author is not None else self.bot.user)

                    if isinstance(ctx, commands.Context):
                        return await ctx.send(embed=embed)

                # There is body so start parsing table
                exams = body.find_all("tr")

                number_of_exams = len(exams)
                bs = config.exams_page_size
                number_of_batches = math.ceil(number_of_exams / bs)
                exam_batches = [exams[i * bs:bs + i * bs] for i in range(number_of_batches)]

                term_strings_dict = {}
                pages = []
                for exam_batch in exam_batches:
                    embed = disnake.Embed(title=title, description=description, color=disnake.Color.dark_blue())
                    utils.add_author_footer(embed, author if author is not None else self.bot.user)

                    for exam in exam_batch:
                        # Every exams row start with link tag
                        tag = exam.find("a") \
                            if str(exam).startswith("<tr><td><a") else None
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
                                    embed.add_field(name=subject_tag, value=col.contents[0],
                                                    inline=False)
                                else:
                                    # Mainly for terms without specified time
                                    term = strong_tag.contents[0].replace(u'\xa0', '').replace(" ", "")

                                    date_splits = term.split(".")
                                    term_datetime = datetime.datetime(int(date_splits[2]),
                                                                      int(date_splits[1]),
                                                                      int(date_splits[0]),
                                                                      23,
                                                                      59)

                                    term_date = datetime.date(int(date_splits[2]),
                                                              int(date_splits[1]),
                                                              int(date_splits[0]))

                                    name = f"{subject_tag}"
                                    term_time = f"{term}\n{col.contents[0]}"

                                    date_offset = " " * (DATE_OFFSET - len(name))
                                    time_offset = " " * (TIME_OFFSET - len(term))
                                    term_string = f"{name}{date_offset}{term}{time_offset}{col.contents[0]}"

                                    if term_date == datetime.date.today():
                                        term_strings_dict[term_datetime] = f"- {term_string}"
                                    elif term_datetime < datetime.datetime.now():
                                        name = f"~~{name}~~"
                                        term_time = f"~~{term_time}~~"
                                    else:
                                        term_strings_dict[term_datetime] = f"+ {term_string}"

                                    embed.add_field(name=name, value=term_time, inline=False)
                            else:
                                # Classic terms
                                whole_term_count = 0
                                for idx, col in enumerate(cols):
                                    terms = col.find_all("strong")
                                    times = col.find_all("em")

                                    number_of_terms = len(terms)
                                    whole_term_count += number_of_terms

                                    for idx2, (term, time) in enumerate(zip(terms, times)):
                                        term = term.contents[0].replace(u'\xa0', '').replace(" ", "")
                                        time_cont = ""
                                        for c in time.contents: time_cont += str(c)
                                        time_cont = time_cont.replace("<sup>", ":").replace("</sup>", "")

                                        date_splits = term.split(".")

                                        try:
                                            # Try to get start time
                                            start_time = time_cont.split("-")[0].replace(" ", "").split(":")
                                            term_datetime = datetime.datetime(int(date_splits[2]),
                                                                              int(date_splits[1]),
                                                                              int(date_splits[0]),
                                                                              int(start_time[0]),
                                                                              int(start_time[1]))
                                        except:
                                            # Failed to get start time so use only date
                                            term_datetime = datetime.datetime(int(date_splits[2]),
                                                                              int(date_splits[1]),
                                                                              int(date_splits[0]),
                                                                              23,
                                                                              59)

                                        term_date = datetime.date(int(date_splits[2]),
                                                                  int(date_splits[1]),
                                                                  int(date_splits[0]))

                                        name = f"{idx + 1}.  {subject_tag}" if number_of_terms == 1 \
                                            else f"{idx + 1}.{idx2 + 1} {subject_tag}"

                                        term_time = f"{term} {time_cont}"

                                        date_offset = " " * (DATE_OFFSET - len(name))
                                        time_offset = " " * (TIME_OFFSET - len(term))
                                        term_string = f"{name}{date_offset}{term}{time_offset}{time_cont}"

                                        if term_date == datetime.date.today():
                                            term_strings_dict[term_datetime] = f"- {term_string}"
                                        elif term_datetime < datetime.datetime.now():
                                            name = f"~~{name}~~"
                                            term_time = f"~~{term_time}~~"
                                        else:
                                            term_strings_dict[term_datetime] = f"+ {term_string}"

                                        embed.add_field(name=name, value=term_time)

                                to_add = math.ceil(whole_term_count / 3) * 3 - whole_term_count
                                for _ in range(to_add):
                                    embed.add_field(name='\u200b', value='\u200b')

                    pages.append(embed)

                number_of_pages = len(pages)
                if number_of_pages > 1:
                    if isinstance(ctx, commands.Context):
                        await PaginatorSession(self.bot, ctx,
                                               timeout=config.exams_paginator_duration,
                                               pages=pages,
                                               color=disnake.Color.dark_blue(),
                                               delete_after=False).run()
                    else:
                        header = disnake.Embed(title=title, description=description, color=disnake.Color.dark_blue())
                        await self.handle_exams_with_database_access(term_strings_dict, header, ctx)
                elif number_of_pages == 1:
                    # Only one page, no need paginator
                    if isinstance(ctx, commands.Context):
                        await ctx.send(embed=pages[0])
                    else:
                        header = disnake.Embed(title=title, description=description, color=disnake.Color.dark_blue())
                        await self.handle_exams_with_database_access(term_strings_dict, header, ctx)
                else:
                    # No pages were parsed, so we will post only default embed
                    embed = disnake.Embed(title=title, description=description, color=disnake.Color.dark_blue())
                    utils.add_author_footer(embed, author if author is not None else self.bot.user)
                    if isinstance(ctx, commands.Context):
                        await ctx.send(embed=embed)
            except:
                # Parsing failed
                embed = disnake.Embed(title=title, description=description, color=disnake.Color.dark_blue())
                utils.add_author_footer(embed, author if author is not None else self.bot.user)
                if isinstance(ctx, commands.Context):
                    await ctx.send(embed=embed)
                    await ctx.send(Messages.exams_parsing_failed)
        else:
            # Site returned fail code
            embed = disnake.Embed(title=title, description=description, color=disnake.Color.dark_blue())
            utils.add_author_footer(embed, author if author is not None else self.bot.user)
            if isinstance(ctx, commands.Context):
                await ctx.send(embed=embed)

    async def handle_exams_with_database_access(self, src_data:dict, header:disnake.Embed,
                                                dest:Union[disnake.TextChannel, disnake.Message]):
        sorted_src_data = collections.OrderedDict(sorted(src_data.items()))
        messages = merge_messages(sorted_src_data.values(), 1900)

        if messages:
            message = messages[0]
            if len(messages) > 1:
                message = f"{message}\n\nZbytek termínu v odkazu"
            src_data_string = f"```diff\n{message}\n```"
        else:
            src_data_string = None

        if isinstance(dest, disnake.TextChannel):
            # No previous message in channel
            send_message = await dest.send(content=src_data_string, embed=header)
            if send_message is not None:
                self.exams_repo.create_term_message(send_message.id, send_message.channel.id)
        else:
            # Message already exists
            await dest.edit(content=src_data_string, embed=header)


def setup(bot):
    bot.add_cog(Exams(bot))
