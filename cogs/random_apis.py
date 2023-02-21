import aiohttp
import contextlib
import random
import re
from typing import List, Dict

import disnake
from disnake.ext import commands
from config import cooldowns
from datetime import datetime

from config.messages import Messages


class RandomApis(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def custom_footer(self, author, url):
        return f"📩 {author} | {url} • {datetime.now().strftime('%d.%m.%Y %H:%M')}"

    @cooldowns.default_cooldown
    @commands.slash_command(name="cat", description=Messages.cat_brief)
    async def cat(self, inter):
        """Get random image of a cat"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.thecatapi.com/v1/images/search"
            ) as response:
                if response.status != 200:
                    await inter.reply(
                        (inter, "Command encountered an error (E{code}).").format(
                            code=response.status
                        )
                    )
                    return
                image_response = await response.json()

            fact_response: str = ""
            if random.randint(0, 9) == 1:
                url: str = "https://meowfacts.herokuapp.com/"

                with contextlib.suppress(OSError):
                    async with session.get(url) as response:
                        if response.status == 200:
                            fact_response_ = await response.json()
                            fact_response = fact_response_["data"][0]

        image_embed = disnake.Embed()
        image_embed.set_footer(text=self.custom_footer(inter.author, "thecatapi.com"))
        image_embed.set_image(url=image_response[0]["url"])
        embeds: List[disnake.Embed] = [image_embed]

        if fact_response:
            fact_embed = disnake.Embed(
                title="Cat fact",
                description=fact_response,
            )
            fact_embed.set_footer(text=self.custom_footer(inter.author, "thecatapi.com"))
            embeds.append(fact_embed)

        await inter.send(embeds=embeds)

    @cooldowns.default_cooldown
    @commands.slash_command(name="dog", description=Messages.dog_brief)
    async def dog(self, inter):
        """Get random image of a dog"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.thedogapi.com/v1/images/search"
            ) as response:
                if response.status != 200:
                    return await inter.reply(
                        (inter, "Command encountered an error (E{code}).").format(
                            code=response.status
                        )
                    )
                image_response = await response.json()

            fact_response: str = ""
            if random.randint(0, 9) == 1:
                with contextlib.suppress(OSError):
                    async with session.get("https://dogapi.dog/api/facts/") as response:
                        if response.status == 200:
                            fact_response_ = await response.json()
                            fact_response = fact_response_["facts"][0]

        image_embed = disnake.Embed()
        image_embed.set_footer(text=self.custom_footer(inter.author, "thedogapi.com"))
        image_embed.set_image(url=image_response[0]["url"])
        embeds: List[disnake.Embed] = [image_embed]

        if fact_response:
            fact_embed = disnake.Embed(
                title="Dog fact",
                description=fact_response,
            )
            fact_embed.set_footer(text=self.custom_footer(inter.author, "thedogapi.com"))
            embeds.append(fact_embed)

        await inter.send(embeds=embeds)

    @cooldowns.default_cooldown
    @commands.slash_command(name="fox", description=Messages.fox_brief)
    async def fox(self, inter):
        """Get random image of a fox"""
        async with aiohttp.ClientSession() as session:
            async with session.get("https://randomfox.ca/floof/") as response:
                if response.status != 200:
                    return await inter.reply(
                        (inter, "Command encountered an error (E{code}).").format(
                            code=response.status
                        )
                    )

                json_response = await response.json()

        embed = disnake.Embed()
        embed.set_footer(text=self.custom_footer(inter.author, "randomfox.ca"))
        embed.set_image(url=json_response["image"])

        await inter.send(embed=embed)

    @cooldowns.default_cooldown
    @commands.slash_command(name="duck", description=Messages.duck_brief)
    async def duck(self, inter):
        """Get random image of a duck"""
        async with aiohttp.ClientSession() as session:
            async with session.get("https://random-d.uk/api/v2/random") as response:
                if response.status != 200:
                    return await inter.reply(
                        (inter, "Command encountered an error (E{code}).").format(
                            code=response.status
                        )
                    )

                json_response = await response.json()

        embed = disnake.Embed()
        embed.set_footer(text=self.custom_footer(inter.author, "random-d.uk"))
        embed.set_image(url=json_response["url"])

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
                await inter.send("I didn't find a joke like that.")
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
            title="Link",
            description=result["joke"],
            url="https://icanhazdadjoke.com/j/" + result["id"],
        )
        embed.set_footer(text=self.custom_footer(inter.author, "icanhazdadjoke.com"))

        await inter.send(embed=embed)


def setup(bot):
    bot.add_cog(RandomApis(bot))
