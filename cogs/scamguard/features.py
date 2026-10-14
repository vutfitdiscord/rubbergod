from io import BytesIO
from pathlib import Path

import dhash
import disnake
from PIL import Image

REFERENCE_IMAGES_DIR = Path(__file__).parent / "reference_images"

# Hamming distance (out of 128 bits) below which an attachment counts as a match.
# Reuses the same dhash approach as warden's repost detection, but with a tighter
# threshold since these scam images are always reposted byte-for-byte identical
# (or only re-compressed), not just visually similar.
MATCH_THRESHOLD = 10


def load_reference_hashes() -> list[int]:
    """Compute dhash for every image bundled in reference_images/.

    Drop additional known scam screenshots into that folder to extend detection.
    """
    hashes = []
    for path in sorted(REFERENCE_IMAGES_DIR.glob("*.jpg")):
        with Image.open(path) as image:
            hashes.append(dhash.dhash_int(image))
    return hashes


async def find_matching_attachment(
    message: disnake.Message, reference_hashes: list[int]
) -> disnake.Attachment | None:
    """Return the first attachment whose dhash is close to a known scam image, if any."""
    for attachment in message.attachments:
        fp = BytesIO()
        try:
            await attachment.save(fp)
            image = Image.open(fp)
        except (disnake.HTTPException, OSError):
            # not an image or failed to download
            continue

        img_hash = dhash.dhash_int(image)
        for ref_hash in reference_hashes:
            if dhash.get_num_bits_different(img_hash, ref_hash) <= MATCH_THRESHOLD:
                return attachment
    return None
