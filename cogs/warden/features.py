from io import BytesIO

import dhash
import disnake
from PIL import Image

from database.image import ImageDB


async def saveMessageHashes(message: disnake.Message):
    for f in message.attachments:
        fp = BytesIO()
        await f.save(fp)
        try:
            image = Image.open(fp)
        except OSError:
            # not an image
            continue
        img_hash = dhash.dhash_int(image)

        ImageDB.add_image(
            channel_id=message.channel.id,
            message_id=message.id,
            attachment_id=f.id,
            dhash=str(hex(img_hash)),
        )
        yield img_hash
