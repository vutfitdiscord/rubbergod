import json
from functools import cached_property
from io import BytesIO

import aiohttp
import disnake
from disnake import Member

import utils
from config.app_config import config
from database import session
from database.verification import PermitDB, ValidPersonDB, VerifyStatus
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
            elif "ustav" in relation.keys() and relation["ustav"]["fakulta"]["zkratka"] == "FIT":
                # FIT employee, replace only if not student
                ret = ret or "employee"
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

    async def get_verified_members(self, guild: disnake.Guild) -> list[disnake.Member]:
        members = guild.members

        verify = disnake.utils.get(guild.roles, name="Verify")
        host = disnake.utils.get(guild.roles, name="Host")
        bot = disnake.utils.get(guild.roles, name="Bot")
        poradce = disnake.utils.get(guild.roles, name="Poradce")
        vut = disnake.utils.get(guild.roles, name="VUT")

        verified = [
            member
            for member in members
            if verify in member.roles
            and host not in member.roles
            and bot not in member.roles
            and poradce not in member.roles
            and vut not in member.roles
        ]

        return verified


    async def get_members_with_unmatching_year(self, guild: disnake.Guild
            ) -> dict[disnake.Role, dict[disnake.Role, list[disnake.Member]]]:
        verified = await self.get_verified_members(guild)

        dropout = disnake.utils.get(guild.roles, name="Dropout")
        survivor = disnake.utils.get(guild.roles, name="Survivor")
        king = disnake.utils.get(guild.roles, name="King")

        dropout_alternatives = [survivor, king]

        years = ["0BIT", "1BIT", "2BIT", "3BIT+", "0MIT", "1MIT", "2MIT+", "Doktorand", "VUT", "Dropout"]

        year_roles = {year: disnake.utils.get(guild.roles, name=year) for year in years}

        unmatching_members: dict[disnake.Role, dict[disnake.Role, list[disnake.Member]]] = {
            year_y: {year_x: [] for year_x in year_roles.values()} for year_y in year_roles.values()
        }

        # collects all members whose database "year" doesn't match their role
        # the first dictionary key is the role they have currently
        # while the value is another dictionary with keys of the role they should have
        for member in verified:
            user = PermitDB.get_user_by_id(member.id)
            if user is None:
                continue
            if len(user) > 1:
                continue

            person = ValidPersonDB.get_user_by_login(user.login)
            if person is None:
                continue

            year = self.verification.transform_year(person.year)

            if year is None:
                year = "Dropout"

            correct_role = disnake.utils.get(guild.roles, name=year)

            if correct_role not in member.roles:
                for role in year_roles.values():
                    if role in member.roles and correct_role in unmatching_members[role].keys():
                        unmatching_members[role][correct_role].append(member)
                        break
                elif not (
                    correct_role == dropout
                    and any(role in member.roles for role in dropout_alternatives)
                ):
                    unmatching_members[dropout][correct_role].append(member)

        return unmatching_members
