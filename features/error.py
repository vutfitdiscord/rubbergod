import datetime
import requests
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

import disnake

from config.app_config import config
from repository.database.error import ErrorLog
import utils


class ErrorLogger:

    def set_image(self, embed: disnake.Embed, user: disnake.User, count: int):
        image_path = Path(__file__).parent.parent / "images/accident"
        background = Image.open(image_path / "xDaysBackground.png")
        head = Image.open(image_path / "xDaysHead.png")
        pliers = Image.open(image_path / "xDaysPliers.png")

        # add avatar
        url = user.display_avatar.with_format('png')
        response = requests.get(url, timeout=10)
        avatarFull = Image.open(BytesIO(response.content))

        if not user.avatar:
            avatarFull = avatarFull.convert("RGB")

        avatarFull.resize((230, 230))
        avatarFull.crop((230, 220))
        background.paste(avatarFull, (560, 270), avatarFull)

        # set number
        font = ImageFont.truetype(image_path / "openSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(background)
        draw.text((1090, 280), count, font=font)

        # add upper layers
        background.paste(head, (0,0), head)
        background.paste(pliers, (0,0), pliers)

        # add image to embed
        with BytesIO() as image_binary:
            background.save(image_binary, format='png')
            image_binary.seek(0)
            file = disnake.File(fp=image_binary, filename="accident.jpg")

        embed.set_image(file=file)

    def log_error_date(self, set=True) -> int:
        """Log date of last exception and return number of days since last exception"""
        try:
            today = datetime.date.today()
            last_exception = ErrorLog.get()
            if last_exception:
                count = (today - last_exception.date).days
            else:
                count = 0
            if set:
                ErrorLog.set()
            return count
        except Exception:
            return None

    def create_embed(
        self, command: str, message: str, author: disnake.User, guild: disnake.Guild, jump_url: str
    ):
        count = self.log_error_date()
        embed = disnake.Embed(
            title=f"{count} days without an accident.\nIgnoring exception in command {command}",
            color=0xFF0000,
        )
        embed.add_field(name="Zpráva", value=message)
        embed.add_field(name="Autor", value=str(author))
        if guild and guild.id != config.guild_id:
            embed.add_field(name="Guild", value=guild.name)
        embed.add_field(name="Link", value=jump_url, inline=False)
        self.set_image(embed, author, count)
        return embed

    async def send_output(self, output: str, channel: disnake.TextChannel):
        output = utils.cut_string(output, 1900)
        if channel is not None:
            for message in output:
                await channel.send(f"```\n{message}\n```")
