"""Inspired by https://github.com/Czechbol/Amadeus/blob/master/cogs/urban.py"""
import datetime
import requests
import asyncio
from urllib import parse as url_parse

import discord
from discord.ext import commands

from config.messages import Messages


class Urban(commands.Cog):
    """Finding expression and shorcuts in urban directory"""

    def __init__(self, bot):
        self.bot = bot

    def urban_embeds(self, ctx, dict):
        """Generate embeds from dictionary of resposes"""
        embed_list = []

        for idx, item in enumerate(dict["list"]):
            definition = item["definition"]
            example = item["example"]

            if len(definition) > 1024:
                definition = definition[0:1021] + "`…`"
            if len(example) > 1024:
                definition = definition[0:1021] + "`…`"

            embed = discord.Embed(
                title=item["word"],
                url=item["permalink"],
            )
            embed.timestamp = datetime.datetime.now(tz=datetime.timezone.utc)
            embed.set_footer(icon_url=ctx.author.avatar_url, text=ctx.author)
            embed.add_field(name="Definition", value=definition, inline=False)
            embed.add_field(name="Example", value=example, inline=False)
            embed.add_field(
                name="Page",
                value=f"{idx + 1}/{len(dict['list'])}",
                inline=False,
            )
            embed_list.append(embed)
        return embed_list

    async def urban_pages(self, ctx, embeds):
        """Send message and handle pagination for 300 seconds"""
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
            if str(reaction.emoji) == "◀️":
                pagenum -= 1
                if pagenum < 0:
                    pagenum = len(embeds) - 1
                try:
                    await message.remove_reaction("◀️", user)
                except discord.errors.Forbidden:
                    pass
                await message.edit(embed=embeds[pagenum])
            if str(reaction.emoji) == "▶️":
                pagenum += 1
                if pagenum >= len(embeds):
                    pagenum = 0
                try:
                    await message.remove_reaction("▶️", user)
                except discord.errors.Forbidden:
                    pass
                await message.edit(embed=embeds[pagenum])


    @commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)
    @commands.command()
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
            embeds = self.urban_embeds(ctx, dict)

        if embeds:
            await self.urban_pages(ctx, embeds)
        else:
            await ctx.send(Messages.urban_not_found)
        return


def setup(bot):
    bot.add_cog(Urban(bot))
