import datetime
import traceback
from io import BytesIO
from pathlib import Path

import disnake
import requests
from PIL import Image, ImageDraw, ImageFont

import utils
from config.app_config import config
from database.error import ErrorLogDB, ErrorRow
from features.imagehandler import ImageHandler


class ErrorLogger:
    def __init__(self):
        self.imagehandler = ImageHandler()

    def set_image(self, embed: disnake.Embed, user: disnake.User, count: int):
        try:
            image_path = Path(__file__).parent.parent / "images/accident"
            background = Image.open(image_path / "xDaysBackground.png")
            head = Image.open(image_path / "xDaysHead.png")
            pliers = Image.open(image_path / "xDaysPliers.png")

            # add avatar
            url = user.display_avatar.replace(size=256, format="png")
            response = requests.get(url, timeout=10)
            avatar = Image.open(BytesIO(response.content))

            if not user.avatar:
                avatar = avatar.convert("RGB")

            avatar = self.imagehandler.square_to_circle(avatar)
            avatar = avatar.resize((230, 230))
            avatar = avatar.crop((0, 0, 230, 200))
            background.paste(avatar, (560, 270), avatar)

            # set number
            font_size = 70 if count >= 10 else 80
            W, H = (150, 150)
            font = ImageFont.truetype(str(image_path / "OpenSans-Regular.ttf"), font_size)
            img_txt = Image.new("RGBA", (W, H), color=(255, 255, 255, 0))
            draw_txt = ImageDraw.Draw(img_txt)
            w, h = draw_txt.textsize(str(count), font=font)
            draw_txt.text(((W - w) / 2, (H - h) / 2), str(count), font=font, fill="#000")
            img_txt = img_txt.rotate(10, expand=1, fillcolor=255)
            background.paste(img_txt, (1005, 145), img_txt)

            # add upper layers
            background.paste(head, (0, 0), head)
            background.paste(pliers, (0, 0), pliers)

            # add image to embed
            with BytesIO() as image_binary:
                background.save(image_binary, format="png")
                image_binary.seek(0)
                file = disnake.File(fp=image_binary, filename="accident.png")

            embed.set_image(file=file)
        except Exception as error:
            output = "".join(traceback.format_exception(type(error), error, error.__traceback__))
            print(output)

    def log_error_date(self, set=True) -> int:
        """Log date of last exception and return number of days since last exception"""
        try:
            today = datetime.date.today()
            last_exception = ErrorLogDB.get(ErrorRow.last_error)
            if last_exception:
                count = (today - last_exception.date).days
            else:
                count = 0
            if set:
                ErrorLogDB.set()
            return count
        except Exception:
            return 0

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
