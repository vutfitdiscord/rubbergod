import disnake
from disnake.ext import commands
import datetime
from typing import Union, List
import re
import requests
from bs4 import BeautifulSoup
import math

from features.paginator import PaginatorSession
from config.app_config import config
from config.messages import Messages
import utils

rocnik_regex = "[1-4][BM]IT"

class Exams(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot

    @commands.command(brief=Messages.exams_brief, aliases=["zkousky"])
    async def exams(self, ctx:commands.Context, rocnik:Union[str, None]=None):
        if rocnik is None:
            if isinstance(ctx.author, disnake.Member):
                user_roles: List[disnake.Role] = ctx.author.roles

                for role in user_roles:
                    match = re.match(rocnik_regex, role.name.upper())

                    if match is not None:
                        rocnik = self.process_match(match)
                        if rocnik is None:
                            return await ctx.send(Messages.exams_no_valid_year)
                        return await self.process_exams(ctx, rocnik)

                await ctx.send(Messages.exams_no_valid_role)
            else:
                try:
                    await ctx.send(Messages.exams_specify_year)
                except:
                    pass
        else:
            match = re.match(rocnik_regex, rocnik.upper())

            if match is not None:
                rocnik = self.process_match(match)
                if rocnik is None:
                    return await ctx.send(Messages.exams_no_valid_year)
                await self.process_exams(ctx, rocnik)
            else:
                await ctx.send(Messages.exams_no_valid_year)

    @staticmethod
    def process_match(match):
        year = match.string[match.regs[0][0]: match.regs[0][1]]
        if year in ("4BIT", "3MIT"):
            year = str(int(year[0]) - 1) + year[1:]

        if year == "4MIT":
            return None
        return year

    async def process_exams(self, ctx:commands.Context, year:Union[str, None]):
        date = datetime.date.today()

        semester = "ZS"
        if 3 < date.month < 9:
            semester = "LS"

        cal_year = date.year
        if semester == "ZS":
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
                    utils.add_author_footer(embed, ctx.author)
                    return await ctx.send(embed=embed)

                exams = body.find_all("tr")

                number_of_exams = len(exams)
                bs = config.exams_page_size
                number_of_batches = math.ceil(number_of_exams / bs)
                exam_batches = [exams[i * bs:bs + i * bs] for i in range(number_of_batches)]

                pages = []
                for exam_batch in exam_batches:
                    embed = disnake.Embed(title=title, description=description, color=disnake.Color.dark_blue())
                    utils.add_author_footer(embed, ctx.author)

                    for exam in exam_batch:
                        tag = exam.find("a")
                        cols = exam.find_all("td")
                        del cols[0]

                        subject_tag = tag.find("strong").contents[0]

                        col_count = len(cols)
                        if col_count == 1:
                            # Support for credits
                            col = cols[0]
                            strong_tag = col.find("strong")

                            if strong_tag is None:
                                # There is no term - Only text
                                embed.add_field(name=subject_tag, value=col.contents[0], inline=False)
                            else:
                                term = str(strong_tag.contents[0]).replace(" ", "")

                                date_splits = term.split(".")
                                term_date = datetime.date(int(date_splits[2]), int(date_splits[1]),
                                                          int(date_splits[0]))

                                name = f"{subject_tag}"
                                term_time = f"{col.contents[0]}\n{term}"
                                if term_date < datetime.date.today():
                                    name = f"~~{name}~~"
                                    term_time = f"~~{term_time}~~"

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
                                    term = str(term.contents[0]).replace(" ", "")
                                    time_cont = ""
                                    for c in time.contents: time_cont += str(c)
                                    time_cont = time_cont.replace("<sup>", ":").replace("</sup>", "")

                                    date_splits = term.split(".")
                                    term_date = datetime.date(int(date_splits[2]), int(date_splits[1]),
                                                              int(date_splits[0]))

                                    name = f"{idx + 1}. {subject_tag}" if number_of_terms == 1 else \
                                        f"{idx + 1}.{idx2 + 1} {subject_tag}"

                                    term_time = f"{term}\n{time_cont}"
                                    if term_date < datetime.date.today():
                                        name = f"~~{name}~~"
                                        term_time = f"~~{term_time}~~"

                                    embed.add_field(name=name, value=term_time)

                            to_add = math.ceil(whole_term_count / 3) * 3 - whole_term_count
                            for _ in range(to_add):
                                embed.add_field(name='\u200b', value='\u200b')

                    pages.append(embed)

                number_of_pages = len(pages)
                if number_of_pages > 1:
                    page_sesstion = PaginatorSession(self.bot, ctx, timeout=config.exams_paginator_duration,
                                                     pages=pages,
                                                     color=disnake.Color.dark_blue(), delete_after=False)

                    await page_sesstion.run()
                elif number_of_pages == 1:
                    # Only one page, no need paginator
                    await ctx.send(embed=pages[0])
                else:
                    # No pages were parsed, so we will post only default embed
                    embed = disnake.Embed(title=title, description=description, color=disnake.Color.dark_blue())
                    utils.add_author_footer(embed, ctx.author)
                    await ctx.send(embed=embed)
            except:
                # Parsing failed
                embed = disnake.Embed(title=title, description=description, color=disnake.Color.dark_blue())
                utils.add_author_footer(embed, ctx.author)
                await ctx.send(embed=embed)
                await ctx.send(Messages.exams_parsing_failed)
        else:
            # Site returned fail code
            embed = disnake.Embed(title=title, description=description, color=disnake.Color.dark_blue())
            utils.add_author_footer(embed, ctx.author)
            await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Exams(bot))
