import discord
from discord.ext import commands
from lxml import etree
import requests

from config.messages import Messages
from utils import add_author_footer

class Studijni(commands.Cog):

    @commands.command(aliases=["studijne", "študijné", "študijní"] ,brief=Messages.studijni_brief)
    async def studijni(self, ctx):
        link = "https://www.fit.vut.cz/fit/room/C109/.cs"
        htmlparser = etree.HTMLParser()
        session = requests.session()
        result = session.get(link)
        xDoc2 = etree.fromstring(result.text, htmlparser)
        hours_div = xDoc2.xpath("//p[b[contains(text(),'Úřední hodiny')]]//following-sibling::div/p")
        hours = etree.tostring(hours_div[0], encoding=str, method="text")
        warning = etree.tostring(hours_div[1], encoding=str, method="text").split(':', 1)
        embed = discord.Embed(title="C109 Studijní oddělení", url=link)
        embed.add_field(name="Úřední hodiny", value=hours, inline=False)
        embed.add_field(name=warning[0], value=warning[1], inline=False)
        add_author_footer(embed, ctx.message.author)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Studijni(bot))
