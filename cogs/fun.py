"""
Here are commands that call random apis for fun things.
examples - animal pictures, dadjokes
"""

import contextlib
import random
import re
from datetime import datetime
from typing import Dict, List

import aiohttp
import disnake
from disnake.ext import commands

from cogs.base import Base
from config import cooldowns
from config.messages import Messages


class Fun(Base, commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def custom_footer(self, author, url):
        return f"📩 {author} | {url} • {datetime.now().strftime('%d.%m.%Y %H:%M')}"

    async def get_image(self, inter, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    await inter.send(
                        "Command encountered an error (E{code}).".format(code=response.status)
                    )
                    return
                image_response = await response.json()
        return image_response

    async def get_fact(self, url, key):
        async with aiohttp.ClientSession() as session:
            with contextlib.suppress(OSError):
                async with session.get(url) as response:
                    if response.status == 200:
                        fact_response_ = await response.json()
                        fact_response = fact_response_[key][0]
        return fact_response

    @cooldowns.default_cooldown
    @commands.slash_command(name="cat", description=Messages.cat_brief)
    async def cat(self, inter):
        """Get random image of a cat"""
        image_response = await self.get_image(inter, "https://api.thecatapi.com/v1/images/search")

        fact_response: str = ""
        if random.randint(0, 9) == 1:
            fact_response = await self.get_fact("https://meowfacts.herokuapp.com/", "data")

        image_embed = disnake.Embed(color=disnake.Color.blue())
        image_embed.set_footer(text=self.custom_footer(inter.author, "thecatapi.com"))
        image_embed.set_image(url=image_response[0]["url"])
        embeds: List[disnake.Embed] = [image_embed]

        if fact_response:
            fact_embed = disnake.Embed(
                title="Cat fact",
                description=fact_response,
                color=disnake.Color.blue(),
            )
            fact_embed.set_footer(text=self.custom_footer(inter.author, "thecatapi.com"))
            embeds.append(fact_embed)

        await inter.send(embeds=embeds)

    @cooldowns.default_cooldown
    @commands.slash_command(name="dog", description=Messages.dog_brief)
    async def dog(self, inter):
        """Get random image of a dog"""
        image_response = await self.get_image(inter, "https://api.thedogapi.com/v1/images/search")

        fact_response: str = ""
        if random.randint(0, 9) == 1:
            fact_response = await self.get_fact("https://dogapi.dog/api/facts/", "facts")

        image_embed = disnake.Embed(color=disnake.Color.blue())
        image_embed.set_footer(text=self.custom_footer(inter.author, "thedogapi.com"))
        image_embed.set_image(url=image_response[0]["url"])
        embeds: List[disnake.Embed] = [image_embed]

        if fact_response:
            fact_embed = disnake.Embed(
                title="Dog fact",
                description=fact_response,
                color=disnake.Color.blue(),
            )
            fact_embed.set_footer(text=self.custom_footer(inter.author, "thedogapi.com"))
            embeds.append(fact_embed)

        await inter.send(embeds=embeds)

    @cooldowns.default_cooldown
    @commands.slash_command(name="fox", description=Messages.fox_brief)
    async def fox(self, inter):
        """Get random image of a fox"""
        image_response = await self.get_image(inter, "https://randomfox.ca/floof/")

        embed = disnake.Embed(color=disnake.Color.blue())
        embed.set_footer(text=self.custom_footer(inter.author, "randomfox.ca"))
        embed.set_image(url=image_response["image"])

        await inter.send(embed=embed)

    @cooldowns.default_cooldown
    @commands.slash_command(name="duck", description=Messages.duck_brief)
    async def duck(self, inter):
        """Get random image of a duck"""
        image_response = await self.get_image(inter, "https://random-d.uk/api/v2/random")

        embed = disnake.Embed(color=disnake.Color.blue())
        embed.set_footer(text=self.custom_footer(inter.author, "random-d.uk"))
        embed.set_image(url=image_response["url"])

        await inter.send(embed=embed)

    @cooldowns.default_cooldown
    @commands.slash_command(name="dadjoke", description=Messages.dadjoke_brief)
    async def dadjoke(self, inter: disnake.ApplicationCommandInteraction, *, keyword=None):
        """Get random dad joke
        Arguments
        ---------
        keyword: search for a certain keyword in a joke
        """
        if keyword is not None and ("&" in keyword or "?" in keyword):
            return await inter.send("I didn't find a joke like that.")

        params: Dict[str, str] = {"limit": "30"}
        url: str = "https://icanhazdadjoke.com"
        if keyword is not None:
            params["term"] = keyword
            url += "/search"
        headers: Dict[str, str] = {"Accept": "application/json"}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                fetched = await response.json()

        if keyword is not None:
            res = fetched["results"]
            if len(res) == 0:
                return await inter.send("I didn't find a joke like that.")
            result = random.choice(res)
            result["joke"] = re.sub(
                f"(\\b\\w*{keyword}\\w*\\b)",
                r"**\1**",
                result["joke"],
                flags=re.IGNORECASE,
            )
        else:
            result = fetched

        embed = disnake.Embed(
            title="Dadjoke",
            description=result["joke"],
            color=disnake.Color.blue(),
            url="https://icanhazdadjoke.com/j/" + result["id"],
        )
        embed.set_footer(text=self.custom_footer(inter.author, "icanhazdadjoke.com"))

        await inter.send(embed=embed)

    @cooldowns.default_cooldown
    @commands.slash_command(name="yo_mamajoke", description=Messages.yo_mamajoke_brief)
    async def yo_mamajoke(self, inter):
        """Get random Yo momma joke"""
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.yomomma.info/") as response:
                if response.status != 200:
                    await inter.send(
                        "Command encountered an error (E{code}).".format(code=response.status)
                    )
                    return
                result = await response.json()

        embed = disnake.Embed(
            title="Yo mamajoke",
            description=result["joke"],
            color=disnake.Color.blue(),
            url="https://yomomma.info",
        )
        embed.set_footer(text=self.custom_footer(inter.author, "yomomma.info"))

        await inter.send(embed=embed)


def setup(bot):
    bot.add_cog(Fun(bot))
