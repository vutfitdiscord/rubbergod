"""Inspired by https://github.com/Czechbol/Amadeus/blob/master/cogs/urban.py"""
import requests

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

    async def urban_pages(self, inter, embeds):
        """Send message and handle pagination for 300 seconds"""
        view = EmbedView(embeds)
        view.message = await inter.edit_original_message(embed=embeds[0], view=view)

    @cooldowns.short_cooldown
    @commands.slash_command(name="urban", description=Messages.urban_brief)
    async def urban(self, inter: disnake.ApplicationCommandInteraction, expression):
        await inter.response.defer(with_message=True)
        embeds = None
        try:
            response = requests.get(f"http://api.urbandictionary.com/v0/define?term={expression}", timeout=10)
            dict = response.json()
            response.raise_for_status()

        except requests.HTTPError as http_err:
            await inter.edit_original_message(f"HTTP error occurred: {http_err}")
        except Exception as err:
            await inter.edit_original_message(f"Error occurred: {err}")
        else:
            # Request was successful
            embeds = self.urban_embeds(inter.author, dict)

        if embeds:
            await self.urban_pages(inter, embeds)
        else:
            await inter.edit_original_message(Messages.urban_not_found)
        return


def setup(bot):
    bot.add_cog(Urban(bot))
