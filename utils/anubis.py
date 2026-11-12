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

# The difficulty is server-supplied. Anything above this is either malicious or
# a server misconfiguration (difficulty 16 already means ~2^64 hashes).
MAX_DIFFICULTY = 16
# Upper bound for solving, so a spiked difficulty can't keep a worker thread
# hashing long after the Discord interaction has expired. The deadline is
# enforced inside the worker, so the thread always terminates on its own.
SOLVE_TIME_LIMIT = 60.0


def _check_deadline(deadline: float) -> None:
    """Abort when the solve budget has been exceeded.

    :raises ApiError: when the deadline has passed
    """
    if time.monotonic() > deadline:
        raise ApiError("Anubis: proof-of-work exceeded the time limit")


def solve_proof_of_work(data: str, difficulty: int, deadline: float) -> tuple[str, int]:
    """Find a nonce so sha256(data + nonce) starts with difficulty zero nibbles.

    :param deadline: monotonic time after which the search is aborted
    :returns: tuple of the hex digest (response) and the nonce
    :raises ApiError: when the deadline is exceeded
    """
    # the worker can start late after waiting in the executor queue, so the
    # deadline has to be checked before the first hash as well
    _check_deadline(deadline)
    prefix = "0" * difficulty
    nonce = 0
    while True:
        digest = hashlib.sha256(f"{data}{nonce}".encode()).hexdigest()
        if digest.startswith(prefix):
            # reject solutions found after the budget expired but before the
            # next periodic check
            _check_deadline(deadline)
            return digest, nonce
        nonce += 1
        if nonce % 4096 == 0:
            _check_deadline(deadline)


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
    difficulty = challenge["difficulty"]
    if not 1 <= difficulty <= MAX_DIFFICULTY:
        raise ApiError(f"Anubis: refusing challenge with difficulty {difficulty}")

    logger.info(f"[Anubis] Solving challenge {challenge['id']} (difficulty {difficulty}) for {response.url}")
    started = time.monotonic()
    response_hex, nonce = await asyncio.to_thread(
        solve_proof_of_work, challenge["randomData"], difficulty, started + SOLVE_TIME_LIMIT
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
        # a rejected solution returns an error page instead of a redirect;
        # check the pass-challenge response itself so that a genuine 404 of
        # the target page (in the redirect chain) is still returned to caller
        pass_response = response.history[0] if response.history else response
        if pass_response.status >= 400:
            raise ApiError(f"Anubis: challenge submission failed (HTTP {pass_response.status})")
        html = await response.text()

    if CHALLENGE_RE.search(html) is not None:
        raise ApiError("Anubis: challenge solution was not accepted")

    return html
