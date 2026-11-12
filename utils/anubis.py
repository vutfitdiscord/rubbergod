"""Solver for the Anubis anti-bot proof-of-work challenge (dspace.vut.cz).

dspace.vut.cz is protected by Anubis, which blocks plain HTTP clients with a
JavaScript proof-of-work challenge. The challenge itself is simple SHA-256
hashcash, so instead of spinning up a headless browser we solve it directly:

1. GET the page, the response contains a challenge (``anubis_challenge`` JSON).
2. Find a nonce such that sha256(random_data + str(nonce)) hex digest starts
   with ``difficulty`` zeros.
3. GET the pass-challenge endpoint with the solution. This sets an auth
   cookie on the session and redirects to the original page.

The auth cookie is stored in the shared aiohttp session cookie jar, so the
challenge is only solved again once the cookie expires.
"""

import asyncio
import hashlib
import json
import logging
import re
import time

import aiohttp

from utils.errors import ApiError

logger = logging.getLogger("rubbergod")

# The challenge is bound to the User-Agent, so it has to stay the same
# for both the challenge and the pass-challenge request.
ANUBIS_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0"
CHALLENGE_RE = re.compile(r'<script id="anubis_challenge" type="application/json">(.*?)</script>', re.S)
PASS_CHALLENGE_URL = "/.within.website/x/cmd/anubis/api/pass-challenge"


def solve_proof_of_work(data: str, difficulty: int) -> tuple[str, int]:
    """Find a nonce so sha256(data + nonce) starts with difficulty zero nibbles.

    :returns: tuple of the hex digest (response) and the nonce
    """
    prefix = "0" * difficulty
    nonce = 0
    while True:
        digest = hashlib.sha256(f"{data}{nonce}".encode()).hexdigest()
        if digest.startswith(prefix):
            return digest, nonce
        nonce += 1


async def anubis_get(session: aiohttp.ClientSession, url: str) -> str:
    """GET a URL and transparently solve an Anubis challenge if present.

    :param session: aiohttp session, cookies are stored in its cookie jar
    :param url: url to fetch
    :returns: html of the target page
    :raises ApiError: when the challenge can't be parsed or solved
    """
    headers = {"User-Agent": ANUBIS_USER_AGENT}

    async with session.get(url, headers=headers) as response:
        html = await response.text()

    match = CHALLENGE_RE.search(html)
    if match is None:
        # no Anubis challenge (or the auth cookie is still valid)
        return html

    challenge = json.loads(match.group(1))["challenge"]
    algorithm = challenge.get("method", "fast")
    if algorithm not in ("fast", "slow"):
        raise ApiError(f"Anubis: unsupported challenge algorithm '{algorithm}'")

    logger.info(
        f"[Anubis] Solving challenge {challenge['id']} "
        f"(difficulty {challenge['difficulty']}) for {response.url}"
    )
    started = time.monotonic()
    response_hex, nonce = await asyncio.to_thread(
        solve_proof_of_work, challenge["randomData"], challenge["difficulty"]
    )
    elapsed = time.monotonic() - started
    logger.info(f"[Anubis] Challenge solved in {elapsed:.2f}s (nonce {nonce})")

    # emulate window.location.replace(pass-challenge?...)
    params = {
        "id": challenge["id"],
        "response": response_hex,
        "nonce": nonce,
        "redir": str(response.url),
        "elapsedTime": f"{int(elapsed * 1000)}",
    }
    pass_url = f"{response.url.origin()}{PASS_CHALLENGE_URL}"
    async with session.get(pass_url, headers=headers, params=params) as response:
        html = await response.text()

    if CHALLENGE_RE.search(html) is not None:
        raise ApiError("Anubis: challenge solution was not accepted")

    return html
