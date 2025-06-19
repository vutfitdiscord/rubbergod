"""
Cog containing commands that call random APIs for fun things.
"""

import contextlib
import os
import random
import re
from datetime import datetime, time
from io import BytesIO
from random import randint

import aiohttp
import disnake
from disnake.ext import commands, tasks

import utils
from cogs.base import Base
from rubbergod import Rubbergod
from utils import cooldowns
from utils.errors import ApiError

from . import features
from .messages_cz import MessagesCZ

fuchs_path = "cogs/fun/fuchs/"
fuchs_list = os.listdir(fuchs_path)

zemle_path = "cogs/fun/zemle/"
zemle_list = os.listdir(zemle_path)


class Fun(Base, commands.Cog):
    def __init__(self, bot: Rubbergod):
        super().__init__()
        self.bot = bot
        self.xkcd_url: str = "https://xkcd.com"
        self.total_xkcd_posts: int = 0

    async def update_xkcd_posts(self):
        xkcd_post = await features.get_xkcd(self.bot.rubbergod_session, f"{self.xkcd_url}/info.0.json")
        self.total_xkcd_posts = xkcd_post["num"]

    async def get_image(self, inter, url) -> tuple[BytesIO, str]:
        async with aiohttp.ClientSession() as session:
            # get random image url
            async with session.get(url) as response:
                if response.status != 200:
                    raise ApiError(response.status)
                image = await response.json()

            # get image url
            if isinstance(image, list):
                url = image[0]["url"]
            else:
                url = image.get("url")
                if not url:
                    url = image.get("image")

            # get image bytes
            async with session.get(url) as response:
                if response.status != 200:
                    raise ApiError(response.status)
                file_name = url.split("/")[-1]
                return BytesIO(await response.read()), file_name

    async def get_fact(self, url, key) -> str:
        async with aiohttp.ClientSession() as session:
            with contextlib.suppress(OSError):
                async with session.get(url) as response:
                    if response.status == 200:
                        fact_response_ = await response.json()
                        fact_response = fact_response_[key][0]
        return fact_response

    @cooldowns.default_cooldown
    @commands.slash_command(name="cat", description=MessagesCZ.cat_brief)
    async def cat(self, inter: disnake.ApplicationCommandInteraction):
        """Get random image of a cat"""
        await inter.response.defer()

        image_bytes, file_name = await self.get_image(inter, "https://api.thecatapi.com/v1/images/search")
        image_file = disnake.File(image_bytes, filename=file_name)

        fact_response: str = ""
        if random.randint(0, 9) == 1:
            fact_response = await self.get_fact("https://meowfacts.herokuapp.com/", "data")

        image_embed = disnake.Embed(color=disnake.Color.blue())
        image_embed.set_footer(text=features.custom_footer(inter.author, "thecatapi.com"))
        image_embed.set_image(file=image_file)
        embeds: list[disnake.Embed] = [image_embed]

        if fact_response:
            fact_embed = disnake.Embed(
                title="Cat fact",
                description=fact_response,
                color=disnake.Color.blue(),
            )
            fact_embed.set_footer(text=features.custom_footer(inter.author, "thecatapi.com"))
            embeds.append(fact_embed)

        await inter.send(embeds=embeds)

    @cooldowns.default_cooldown
    @commands.slash_command(name="dog", description=MessagesCZ.dog_brief)
    async def dog(self, inter: disnake.ApplicationCommandInteraction):
        """Get random image of a dog"""
        await inter.response.defer()

        image_bytes, file_name = await self.get_image(inter, "https://api.thedogapi.com/v1/images/search")
        image_file = disnake.File(image_bytes, filename=file_name)

        fact_response: str = ""
        if random.randint(0, 9) == 1:
            fact_response = await self.get_fact("https://dogapi.dog/api/facts/", "facts")

        image_embed = disnake.Embed(color=disnake.Color.blue())
        image_embed.set_footer(text=features.custom_footer(inter.author, "thedogapi.com"))
        image_embed.set_image(file=image_file)
        embeds: list[disnake.Embed] = [image_embed]

        if fact_response:
            fact_embed = disnake.Embed(
                title="Dog fact",
                description=fact_response,
                color=disnake.Color.blue(),
            )
            fact_embed.set_footer(text=features.custom_footer(inter.author, "thedogapi.com"))
            embeds.append(fact_embed)

        await inter.send(embeds=embeds)

    @cooldowns.default_cooldown
    @commands.slash_command(name="fox", description=MessagesCZ.fox_brief)
    async def fox(self, inter: disnake.ApplicationCommandInteraction):
        """Get random image of a fox"""
        await inter.response.defer()

        image_bytes, file_name = await self.get_image(inter, "https://randomfox.ca/floof/")
        image_file = disnake.File(image_bytes, filename=file_name)

        embed = disnake.Embed(color=disnake.Color.blue())
        embed.set_footer(text=features.custom_footer(inter.author, "randomfox.ca"))
        embed.set_image(file=image_file)

        await inter.send(embed=embed)

    @cooldowns.default_cooldown
    @commands.slash_command(name="duck", description=MessagesCZ.duck_brief)
    async def duck(self, inter: disnake.ApplicationCommandInteraction):
        """Get random image of a duck"""
        await inter.response.defer()

        image_bytes, file_name = await self.get_image(inter, "https://random-d.uk/api/v2/random")
        image_file = disnake.File(image_bytes, filename=file_name)

        embed = disnake.Embed(color=disnake.Color.blue())
        embed.set_footer(text=features.custom_footer(inter.author, "random-d.uk"))
        embed.set_image(file=image_file)

        await inter.send(embed=embed)

    @cooldowns.default_cooldown
    @commands.slash_command(name="dadjoke", description=MessagesCZ.dadjoke_brief)
    async def dadjoke(self, inter: disnake.ApplicationCommandInteraction, *, keyword=None):
        """Get random dad joke
        Arguments
        ---------
        keyword: search for a certain keyword in a joke
        """
        await inter.response.defer()

        if keyword is not None and ("&" in keyword or "?" in keyword):
            await inter.send("I didn't find a joke like that.")
            return

        params: dict[str, str] = {"limit": "30"}
        url: str = "https://icanhazdadjoke.com"
        if keyword is not None:
            params["term"] = keyword
            url += "/search"
        headers: dict[str, str] = {"Accept": "application/json"}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status != 200:
                    raise ApiError(response.status)
                fetched = await response.json()

        if keyword is not None:
            res = fetched["results"]
            if len(res) == 0:
                await inter.send("I didn't find a joke like that.")
                return
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
        embed.set_footer(text=features.custom_footer(inter.author, "icanhazdadjoke.com"))

        await inter.send(embed=embed)

    @cooldowns.default_cooldown
    @commands.slash_command(name="yo_mamajoke", description=MessagesCZ.yo_mamajoke_brief)
    async def yo_mamajoke(self, inter: disnake.ApplicationCommandInteraction):
        """Get random Yo momma joke"""
        await inter.response.defer()

        async with aiohttp.ClientSession() as session:
            async with session.get("https://www.yomama-jokes.com/api/v1/jokes/random/") as response:
                if response.status != 200:
                    raise ApiError(response.status)
                result = await response.json()

        embed = disnake.Embed(
            title="Yo mamajoke",
            description=result["joke"],
            color=disnake.Color.blue(),
            url="https://www.yomama-jokes.com",
        )
        embed.set_footer(text=features.custom_footer(inter.author, "https://www.yomama-jokes.com/"))

        await inter.send(embed=embed)

    @cooldowns.default_cooldown
    @commands.slash_command(name="fuchs", description=MessagesCZ.fuchs_brief)
    async def fuchs(
        self,
        inter: disnake.ApplicationCommandInteraction,
        hlaskaid: int = commands.Param(default=None, ge=1, le=len(fuchs_list)),
    ):
        await inter.response.defer()

        if len(fuchs_list) == 0:
            inter.send(MessagesCZ.fuchs_no_reaction)
            return

        if hlaskaid is None:
            index = randint(1, len(fuchs_list))
        else:
            index = hlaskaid

        embed = disnake.Embed(
            title="Fuchs reakce",
            color=disnake.Color.blue(),
        )
        embed.set_image(url=f"attachment://{str(index)}.png")

        utils.embed.add_author_footer(embed, inter.author, additional_text=[f" (hláškaid: #{str(index)})"])

        with open(fuchs_path + str(index) + ".png", "rb") as fp:
            await inter.send(embed=embed, file=disnake.File(fp=fp, filename=str(index) + ".png"))

    @cooldowns.default_cooldown
    @commands.slash_command(name="xkcd", description=MessagesCZ.xkcd_brief)
    async def xkcd(
        self,
        inter: disnake.ApplicationCommandInteraction,
        number: int = commands.Param(default=None, ge=1),
        latest: bool = False,
    ):
        """Get random XKCD comic.
        If `latest` is specified, get the latest comic.
        If `number` is specified, get the comic with that number.
        If `number` and `latest` is specified, get comic with specified number.
        """
        await inter.response.defer()
        if not self.total_xkcd_posts:
            await self.update_xkcd_posts()

        if number:
            url = f"{self.xkcd_url}/{number}"
        elif latest:
            url = f"{self.xkcd_url}"
        else:
            number = random.randint(1, self.total_xkcd_posts)
            url = f"{self.xkcd_url}/{number}"

        xkcd_post = await features.get_xkcd(self.bot.rubbergod_session, f"{url}/info.0.json")
        if latest:
            # Make the latest comic static
            url += f"/{xkcd_post['num']}"
        embed = await features.create_xkcd_embed(xkcd_post, inter.author, url)
        await inter.send(embed=embed)

    @cooldowns.default_cooldown
    @commands.slash_command(name="zemle", description=MessagesCZ.zemle_brief)
    async def zemle(self, inter: disnake.ApplicationCommandInteraction):
        """Get random image of a bun"""
        await inter.response.defer()

        if len(zemle_list) == 0:
            await inter.send("Žádná žemle není k dispozici.")
            return

        zemle_name = random.choice(zemle_list)
        embed = disnake.Embed(
            title="Náhodná žemle",
            color=disnake.Color.blue(),
        )
        embed.set_image(url=f"attachment://{zemle_name}")
        embed.set_footer(text=features.custom_footer(inter.author, "žemle"))

        with open(zemle_path + zemle_name, "rb") as fp:
            await inter.send(embed=embed, file=disnake.File(fp=fp, filename=zemle_name))

    @tasks.loop(time=time(12, 0, tzinfo=utils.general.get_local_zone()))
    async def xkcd_task_update(self):
        """Update number of xkcd comics every sunday"""
        if datetime.today().isoweekday() != 7:
            # update only on sunday
            return

        await self.update_xkcd_posts()
