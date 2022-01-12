import discord
from discord.ext import commands
import datetime
from typing import Union, List
import re
import requests
from bs4 import BeautifulSoup
import math

from features.paginator import PaginatorSession
from config.app_config import Config as config
from config.messages import Messages
import utils

rocnik_regex = "[1-4][BM]IT"

class Exams(commands.Cog):
  def __init__(self, bot:commands.Bot):
    self.bot = bot

  @commands.command(brief=Messages.exams_brief, aliases=["zkousky"])
  async def exams(self, ctx:commands.Context, rocnik:Union[str, None]=None):
    if rocnik is None:
      user_roles: List[discord.Role] = ctx.author.roles

      for role in user_roles:
        match = re.match(rocnik_regex, role.name)

        if match is not None:
          rocnik = self.process_match(match)
          return await self.process_exams(ctx, rocnik)

      await ctx.send(Messages.exams_no_valid_role)
    else:
      match = re.match(rocnik_regex, rocnik)
      if match is not None:
        rocnik = self.process_match(match)
        await self.process_exams(ctx, rocnik)
      else:
        await ctx.send(Messages.exams_no_valid_year)

  @staticmethod
  def process_match(match):
    year = match.string[match.regs[0][0]: match.regs[0][1]]
    if year in ("4BIT", "3MIT"):
      year = str(int(year[0]) - 1) + year[1:]
    return year

  async def process_exams(self, ctx:commands.Context, year:Union[str, None]):
    date = datetime.date.today()

    semester = "ZS"
    if 3 < date.month < 9:
      semester = "LS"

    cal_year = date.year
    if semester == "ZS":
      cal_year -= 1

    year_url = f"https://minerva3.fit.vutbr.cz/rozvrhis/{semester}{cal_year}/zkousky/{year}"
    all_url = f"https://minerva3.fit.vutbr.cz/rozvrhis/{semester}{cal_year}/zkousky"
    description = f"[{year}]({year_url})\n" if year else ""
    description += f"[Odkaz na všechny zkoušky]({all_url})"

    title = f"Zkoušky {year} {semester}{cal_year}-{cal_year + 1}" \
      if year else f"Zkoušky {semester}{cal_year}-{cal_year + 1}"

    r = requests.get(year_url)
    if r.status_code == 200:
      soup = BeautifulSoup(r.content, 'html.parser')

      try:
        table = soup.find("table", {"class": "exam"})
        body = table.find("tbody")
        exams = body.find_all("tr")

        number_of_exams = len(exams)
        number_of_batches = math.ceil(number_of_exams / config.exams_page_size)
        exam_batches = [exams[i * config.exams_page_size:config.exams_page_size + i * config.exams_page_size] for i in range(number_of_batches)]

        pages = []
        for exam_batch in exam_batches:
          embed = discord.Embed(title=title, description=description, color=discord.Color.dark_blue())
          utils.add_author_footer(embed, ctx.author)

          for exam in exam_batch:
            tag = exam.find("a")
            rows = exam.find_all("td")
            del rows[0]

            subject_tag = tag.find("strong").contents[0]

            for idx, row in enumerate(rows):
              termin = str(row.find("strong").contents[0]).replace(" ", "")
              time_cont = ""
              for c in row.find("em").contents: time_cont += str(c)
              time_cont = time_cont.replace("<sup>", ":").replace("</sup>", "")

              date_splits = termin.split(".")
              termin_date = datetime.date(int(date_splits[2]), int(date_splits[1]), int(date_splits[0]))

              termin_name = f"{idx + 1}. {subject_tag}"
              termin_time = f"{termin}\n{time_cont}"
              if termin_date < datetime.date.today():
                termin_name = "~~" + termin_name + "~~"
                termin_time = "~~" + termin_time + "~~"

              embed.add_field(name=termin_name, value=termin_time)

          pages.append(embed)

        number_of_pages = len(pages)
        if number_of_pages > 1:
          page_sesstion = PaginatorSession(self.bot, ctx, timeout=config.exams_paginator_duration,
                                           pages=pages,
                                           color=discord.Color.dark_blue(), delete_after=False)

          await page_sesstion.run()
        elif number_of_pages > 0:
          await ctx.send(embed=pages[0])
        else:
          embed = discord.Embed(title=title, description=description, color=discord.Color.dark_blue())
          utils.add_author_footer(embed, ctx.author)
          await ctx.send(embed=embed)
      except:
        embed = discord.Embed(title=title, description=description, color=discord.Color.dark_blue())
        utils.add_author_footer(embed, ctx.author)
        await ctx.send(embed=embed)
    else:
      embed = discord.Embed(title=title, description=description, color=discord.Color.dark_blue())
      utils.add_author_footer(embed, ctx.author)
      await ctx.send(embed=embed)

def setup(bot):
  bot.add_cog(Exams(bot))
