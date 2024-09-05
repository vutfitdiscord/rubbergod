import json
from functools import cached_property
from io import BytesIO

import aiohttp
import disnake
from disnake import Member

import utils
from config.app_config import config
from database import session
from database.verification import ValidPersonDB, VerifyStatus
from rubbergod import Rubbergod


class VerifyHelper:
    def __init__(self, bot: Rubbergod) -> None:
        self.bot = bot

    @cached_property
    def log_channel(self):
        return self.bot.get_channel(config.log_channel)

    async def has_role(self, user, role_name: str) -> bool:
        if isinstance(user, Member):
            return utils.user.has_role(user, role_name)
        else:
            guild = await self.bot.fetch_guild(config.guild_id)
            member = await guild.fetch_member(user.id)
            return utils.user.has_role(member, role_name)

    async def get_user_details(self, id: str) -> dict | None:
        headers = {"Authorization": f"Bearer {config.vut_api_key}"}
        url = f"https://www.vut.cz/api/person/v1/{id}/pusobeni-osoby"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as res:
                if res.status != 200:
                    if res.status in [401, 403]:
                        raise Exception("Invalid API key")
                    elif res.status == 429:
                        raise Exception("Rate limit exceeded")
                    # Login not found
                    return None
                return await res.json()

    async def _parse_relation(self, user: dict) -> str | None:
        """Parse user relations and return year, programee and faculty for students,
        `employee` for FIT employees, None for others."""
        ret = None  # rule out students that are also employees or have multiple studies
        relation: dict
        for relation in user["vztahy"]:
            # student
            if "rok_studia" in relation.keys():
                ret = (
                    f"{relation['fakulta']['zkratka']} {relation['obor']['zkratka']} "
                    f"{relation['rok_studia'] if relation['rok_studia'] != 1 else 0}"
                )  # this will need fixing before ~septeber 2024 but the best we can do right now
                # do not return yet if not FIT, check for all relations if student has multiple studies
                if relation["fakulta"]["zkratka"] == "FIT":
                    return ret
            elif "fakulta" in relation.keys():
                if relation["fakulta"]["zkratka"] == "FIT":
                    # FIT employee, replace only if not student
                    ret = ret or "employee"
                else:
                    ret = ret or "external employee"
        if not ret:
            await self.log_relation_error(user)
        return ret

    async def save_user_details(self, user: dict) -> ValidPersonDB:
        """Save user details to database and return the user object."""
        # search for login in database
        person = None
        if user.get("login") is not None:
            person = ValidPersonDB.get_user_by_login(user["login"].strip())
        if person is None:
            # search for id in database
            person = ValidPersonDB.get_user_by_login(str(user["id"]))
        if person is None:
            # user not found in DB, add new user
            person = ValidPersonDB(
                login=user.get("login") or str(user["id"]),
                year=await self._parse_relation(user),
                name=f"{user['jmeno_krestni']} {user['prijmeni']}",
                mail=user["emaily"][0] if user.get("emaily", []) else "",
                status=VerifyStatus.Unverified.value,
            )
            session.add(person)
            session.commit()
        else:
            relation = await self._parse_relation(user)
            if person.year != relation:
                person.year = relation
                session.commit()
        return person

    async def check_api(self, id: str) -> ValidPersonDB | None:
        user = await self.get_user_details(id)
        if user is None:
            return None
        person = await self.save_user_details(user)
        return person

    async def get_mails(self, id: str) -> list[str]:
        user = await self.get_user_details(id)
        return user["emaily"] if user else []

    async def log_relation_error(self, user: dict) -> None:
        name = user["login"] or user["id"]
        with BytesIO(bytes(json.dumps(user, indent=2, ensure_ascii=False), "utf-8")) as file:
            file = disnake.File(fp=file, filename=f"{name}.json")
        await self.log_channel.send(f"Error parsing user relations for `{name}`", file=file)
