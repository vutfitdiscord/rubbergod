import re

import disnake


def extract_poll_id(inter: disnake.MessageInteraction) -> int:
    """extracts the report id from the footer of the report embed"""
    poll_id = re.match(r".+ \| ID: (\d+).*", inter.message.embeds[0].footer.text).group(1)
    return int(poll_id)
