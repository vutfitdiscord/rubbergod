
import io
import json
from typing import List, Union

import disnake

import utils

pin_channel_type = Union[
    disnake.TextChannel,
    disnake.Thread
]


class AutopinFeatures():
    def __init__(self, bot):
        self.bot = bot

    async def create_json_file(
            self,
            channel: pin_channel_type,
            pins: List[disnake.Message],
    ):
        """Create json file with all pins from channel"""
        if hasattr(channel, "name"):
            channel_name = channel.name
            channel_url = channel.jump_url
        else:
            channel_name = self.bot.user.name
            channel_url = ""
        list_pins = []
        for pin in pins:
            created_at = pin.created_at.astimezone(tz=utils.get_local_zone()).replace(tzinfo=None)
            dict_pin = {
                "author": pin.author.name,
                "created_at": created_at.isoformat("T", "seconds"),
                "jump_url": pin.jump_url,
                "content": pin.content,
                "attachments": [{"name": file.filename, "url": file.url} for file in pin.attachments]
            }
            list_pins.append(dict_pin)

        dict_pins = {"channel_name": channel_name, "channel_url": channel_url, "pins": list_pins}
        json_pins = json.dumps(dict_pins, indent=4)
        with io.StringIO() as f:
            f.write(json_pins)
            f.seek(0)
            return disnake.File(f, filename=f"{channel_name}_pins.json")

    async def create_markdown_file(
            self,
            channel: pin_channel_type,
            pins: List[disnake.Message]
    ):
        """Create markdown file with all pins from channel"""
        if hasattr(channel, "name"):
            channel_name = channel.name
            channel_url = channel.jump_url
        else:
            channel_name = self.bot.user.name
            channel_url = ""

        with io.StringIO() as f:
            f.write(f"# [#{channel_name}]({channel_url})\n\n")
            for index, pin in enumerate(pins):
                created_at = pin.created_at.astimezone(tz=utils.get_local_zone()).replace(tzinfo=None)
                f.write(f"## {index+1}. {pin.author} — {created_at.strftime('%d. %m. %Y %H:%M:%S')}\n\n")
                f.write(f"[Message link]({pin.jump_url})\n\n")
                f.write(f"### Content\n\n{pin.content}\n\n") if pin.content else ...
                files = ""
                for file in pin.attachments:
                    if file.content_type is not None and "image" in file.content_type:
                        files += f"![{file.filename}]({file.url}); \n"
                    else:
                        files += f"[{file.filename}]({file.url}); \n"
                f.write(f"### Attachments\n\n{files}\n\n") if files else ...
                f.write("---\n\n")
            f.seek(0)
            return disnake.File(f, filename=f"{channel_name}_pins.md")
