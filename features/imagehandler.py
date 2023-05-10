"""
Helper functions for image manipulation and creation of gifs.
"""

from io import BytesIO
from pathlib import Path
from typing import List

from PIL import Image, ImageDraw


class ImageHandler:
    def square_to_circle(self, image: Image.Image) -> Image.Image:
        width, height = image.size
        mask = Image.new("L", (width, height), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, width, height), fill=255)
        alpha = image.getchannel("A")
        circle_alpha = Image.new("L", (width, height), 0)
        circle_alpha.paste(alpha, mask=mask)
        result = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        result.paste(image, (0, 0), mask=circle_alpha)
        return result

    def render_catnap(self, image_binary: BytesIO, avatar: Image, avatar_offset=(48, 12)):
        speed = 60
        hop_size = 4
        frame_count = 11

        image_path = Path(__file__).parent.parent / "images" / "cat_steal"

        im = Image.new("RGBA", (150, 200), (0, 0, 0, 0))

        background = Image.open(image_path / "catyay.png").convert("RGBA")
        catpaw = Image.open(image_path / "catpaw.png").convert("RGBA")

        x, y = avatar_offset
        width, height = 150, 150
        im.paste(background, (38//2, 38 + 50), background)
        im.paste(avatar, (x, y+50), avatar)
        im.paste(catpaw, (38//2, 38 + 50), catpaw)
        im2 = im.transpose(Image.FLIP_LEFT_RIGHT)

        frames = []
        for i in range(frame_count):
            im = im.convert("RGBA")
            frame = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            hop = 12 if i % 2 else 12+hop_size
            frame.paste(im, (i*10 - 50, hop - 50), im)
            frames.append(frame)
            del frame
        for i in range(frame_count):
            im2 = im2.convert("RGBA")
            frame = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            hop = 12+hop_size if i % 2 else 12
            frame.paste(im2, ((10-i)*10 - 50, hop - 50), im2)
            frames.append(frame)

        frames[0].save(
            image_binary,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=speed,
            loop=0,
            transparency=0,
            disposal=2,
            optimize=False,
        )
        image_binary.seek(0)

    def get_bonk_frames(self, avatar: Image.Image) -> List[Image.Image]:
        """Get frames for the bonk"""
        frames = []
        width, height = 200, 170
        deformation = (0, 0, 0, 5, 10, 20, 15, 5)

        avatar = self.square_to_circle(avatar.resize((100, 100)))

        for i in range(8):
            img = "%02d" % (i + 1)
            frame = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            bat = Image.open(f"images/bonk/{img}.png").convert("RGBA")
            avatar = avatar.resize((100, 100 - deformation[i]))
            frame_avatar = avatar.convert("P", palette=Image.ADAPTIVE, colors=200).convert("RGBA")

            frame.paste(frame_avatar, (80, 60 + deformation[i]), frame_avatar)
            frame.paste(bat, (10, 5), bat)
            frames.append(frame)

        return frames
