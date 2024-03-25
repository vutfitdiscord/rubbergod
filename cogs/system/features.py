import os
import re

import disnake
from disnake.ext import commands
from genericpath import isdir, isfile


from . import features
from .messages_cz import MessagesCZ


def get_all_cogs() -> list[tuple[str, str]]:
    """Get all cog modules"""
    path = "./cogs"
    all_cogs = []

    for name in os.listdir("./cogs"):
        filepath = f"./cogs/{name}"

        # ignore __init__.py, non-python files and folders/non-existent files
        if name in ignored or not name.endswith(".py") or not isfile(filepath):
            continue

        # get all cog classes
        with open(os.path.join("./cogs", name), "r") as file:
            contents = file.read()
            match = cog_pattern.findall(contents)
            if match:
                all_cogs[match[0].lower()] = match[0]

    all_cogs = {key: all_cogs[key] for key in sorted(all_cogs.keys())}
    return all_cogs
