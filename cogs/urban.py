"""Inspired by https://github.com/Czechbol/Amadeus/blob/master/cogs/urban.py"""
import requests
import asyncio
from urllib import parse as url_parse

import discord
from discord.ext import commands

import utils
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

            embed = discord.Embed(
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
        try:
            message = await ctx.send(embed=embeds[0])
        except discord.errors.HTTPException:
            # not well formed url, API bug
            embeds[0].url = ""
            message = await ctx.send(embed=embeds[0])

        pagenum = 0
        await message.add_reaction("◀️")
        await message.add_reaction("▶️")
        while True:

            def check(reaction, user):
                return (
                    reaction.message.id == message.id
                    and (str(reaction.emoji) == "◀️" or str(reaction.emoji) == "▶️")
                    and user != self.bot.user
                )

            try:
                reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=300.0)
            except asyncio.TimeoutError:
                return
            emoji = str(reaction.emoji)
            if emoji == "◀️":
                pagenum -= 1
                if pagenum < 0:
                    pagenum = len(embeds) - 1
            elif emoji == "▶️":
                pagenum += 1
                if pagenum >= len(embeds):
                    pagenum = 0
            try:
                await message.remove_reaction(emoji, user)
            except discord.errors.Forbidden:
                pass

            try:
                await message.edit(embed=embeds[pagenum])
            except discord.errors.HTTPException:
                # not well formed url, API bug
                embeds[pagenum].url = ""
                await message.edit(embed=embeds[pagenum])

    @commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)
    @commands.command(brief=Messages.urban_brief)
    async def urban(self, ctx, *expression):
        if not len(expression):
            await ctx.send(Messages.urban_help)
            return
        term = url_parse.quote(" ".join(expression))
        embeds = None
        try:
            response = requests.get(f"http://api.urbandictionary.com/v0/define?term={term}")
            dict = response.json()
            response.raise_for_status()

        except requests.HTTPError as http_err:
            await ctx.send(f"HTTP error occurred: {http_err}")
        except Exception as err:
            await ctx.send(f"Error occurred: {err}")
        else:
            # Request was successful
            embeds = self.urban_embeds(ctx.author, dict)

        if embeds:
            await self.urban_pages(ctx, embeds)
        else:
            await ctx.send(Messages.urban_not_found)
        return


def setup(bot):
    bot.add_cog(Urban(bot))
