"""Inspired by https://github.com/Czechbol/Amadeus/blob/master/cogs/urban.py"""
import requests
from urllib import parse as url_parse

import disnake
from disnake.ext import commands
from buttons.embed import EmbedView

import utils
from config import cooldowns
from config.messages import Messages


class Urban(commands.Cog):
    """Finding expression and shorcuts in urban directory"""

    def __init__(self, bot):
        self.bot = bot

    def urban_embeds(self, author, dict):
        """Generate embeds from dictionary of resposes"""
        embed_list = []

        for idx, item in enumerate(dict["list"]):
            definition = item["definition"]
            example = item["example"]

            if len(definition) > 1024:
                definition = definition[0:1021] + "`…`"
            if len(example) > 1024:
                example = example[0:1021] + "`…`"

            embed = disnake.Embed(
                title=item["word"],
                url=item["permalink"],
            )
            embed.add_field(name="Definition", value=definition, inline=False)
            if example:
                embed.add_field(name="Example", value=example, inline=False)
            embed.add_field(
                name="Page",
                value=f"{idx + 1}/{len(dict['list'])}",
                inline=False,
            )
            utils.add_author_footer(embed, author)

            embed_list.append(embed)

        return embed_list

    async def urban_pages(self, ctx, embeds):
        """Send message and handle pagination for 300 seconds"""
        await ctx.reply(embed=embeds[0], view=EmbedView(embeds))

    @cooldowns.short_cooldown
    @commands.command(brief=Messages.urban_brief)
    async def urban(self, ctx, *expression):
        if not len(expression):
            await ctx.reply(Messages.urban_help)
            return
        term = url_parse.quote(" ".join(expression))
        embeds = None
        try:
            response = requests.get(f"http://api.urbandictionary.com/v0/define?term={term}")
            dict = response.json()
            response.raise_for_status()

        except requests.HTTPError as http_err:
            await ctx.reply(f"HTTP error occurred: {http_err}")
        except Exception as err:
            await ctx.reply(f"Error occurred: {err}")
        else:
            # Request was successful
            embeds = self.urban_embeds(ctx.author, dict)

        if embeds:
            await self.urban_pages(ctx, embeds)
        else:
            await ctx.reply(Messages.urban_not_found)
        return


def setup(bot):
    bot.add_cog(Urban(bot))
