import datetime
from io import BytesIO
from pathlib import Path

import disnake

from config.app_config import config
from repository.database.error import ErrorLog
import utils


class ErrorLogger:

    def set_image(self, embed):
        image_path = Path(__file__).parent.parent / "images/accident.jpg"
        with image_path.open("rb") as handle:
            data = BytesIO(handle.read())
        file = disnake.File(fp=data, filename="accident.jpg")
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
        self.set_image(embed)
        return embed

    async def send_output(self, output: str, channel: disnake.TextChannel):
        output = utils.cut_string(output, 1900)
        if channel is not None:
            for message in output:
                await channel.send(f"```\n{message}\n```")
