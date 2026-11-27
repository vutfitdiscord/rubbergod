"""
Cog for diploma verification. When successful, the user is given Survivor(Bc.) or King(Ing.) role.
"""

import asyncio
import logging
import re
import unicodedata

import aiohttp
import disnake
from disnake.ext import commands
from lxml import etree

from cogs.base import Base
from database.verification import ValidPersonDB
from rubbergod import Rubbergod
from utils.anubis import anubis_get
from utils.errors import ApiError

from .messages_cz import MessagesCZ


class Absolvent(Base, commands.Cog):
    def __init__(self, bot: Rubbergod):
        super().__init__()
        self.logger = logging.getLogger("rubbergod")
        self.bot = bot

    @commands.slash_command(name="diplom_help", description=MessagesCZ.diplom_help_brief)
    async def diplom_help(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.send_message(MessagesCZ.diplom_help_print)

    @commands.slash_command(name="diplom", description=MessagesCZ.diplom_brief)
    async def diplom(
        self,
        inter: disnake.ApplicationCommandInteraction,
        degree: str = commands.Param(choices=["Bc.", "Ing."], description=MessagesCZ.degree_param),
        name: str = commands.Param(description=MessagesCZ.name_param),
        surname: str = commands.Param(description=MessagesCZ.surname_param),
        diploma_number: str = commands.Param(description=MessagesCZ.diploma_param),
        thesis_web_id: int = commands.Param(description=MessagesCZ.thesis_id_param),
    ):
        """Command for diploma verification and honourable role addition

        :param inter: disnake interaction
        :param name: first name (case-sensitive)
        :param surname: last name (case-sensitive)
        :param degree: strictly either "Bc." or "Ing." (case-sensitive)
        :param diploma_number: ID of diploma, in format NNNNNN/YYYY
        :param thesis_web_id: ID from URL http://hdl.handle.net/11012/<num>
            can be discovered via http://hdl.handle.net/11012/19121
        """
        await inter.response.defer(ephemeral=True)

        author = await self.base_guild.fetch_member(inter.author.id)
        if not author:
            # user is not on the server
            await inter.edit_original_response(MessagesCZ.not_on_server(user=inter.author.id))
            return

        verify_role = self.base_guild.get_role(self.config.verification_role_id)
        if verify_role not in author.roles:
            # check whether the user is verified
            await inter.edit_original_response(MessagesCZ.not_verified)
            return

        if thesis_web_id == "19121":
            await inter.edit_original_response(MessagesCZ.id_from_help)
            return

        # prepare
        htmlparser = etree.HTMLParser()
        diploma = re.search(r"\d+/(\d+)", diploma_number)
        if not diploma:
            await inter.edit_original_response(MessagesCZ.wrong_diploma_format)
            return
        diploma_year = diploma.group(1)
        name = " ".join(name.split())
        surname = " ".join(surname.split())

        # CHECK WHETHER THE PROVIDED NAME MATCHES THE ONE STORED FOR FIT VUT VERIFICATION

        def remove_accents(input_str):
            nfkd_form = unicodedata.normalize("NFKD", input_str)
            only_ascii = nfkd_form.encode("ASCII", "ignore").decode("ASCII")
            return only_ascii

        # get name for bot database for the current command caller
        name_from_db = ValidPersonDB.get_user_by_id(inter.author.id)

        if name_from_db is None or not name_from_db.name:
            await inter.edit_original_response(MessagesCZ.not_in_db)
            return

        # Compare normalized word multisets (without accents) to handle both
        # "First [Middle] Last" (VUT API) and "Last First [Middle]" (legacy DB)
        # regardless of how middle names or multiple surnames were split.
        name_from_user_words = sorted(remove_accents(f"{name} {surname}").split())
        name_from_db_words = sorted(remove_accents(name_from_db.name).split())
        if name_from_db_words != name_from_user_words:
            await inter.edit_original_response(MessagesCZ.wrong_name)
            return

        # CHECK OWNERSHIP, TYPE AND YEAR OF THE QUALIFICATION WORK / THESIS
        original_msg = await self.append_response(inter, "", MessagesCZ.status_thesis)

        thesis_url = f"http://hdl.handle.net/11012/{thesis_web_id}?locale-attribute=cs"

        # download the page, solving the Anubis anti-bot challenge if needed
        try:
            result_thesis = await anubis_get(self.bot.rubbergod_session, thesis_url)
        except (aiohttp.ClientConnectorError, asyncio.TimeoutError) as error:
            raise ApiError(str(error))

        # parse it using lxml
        xDoc_thesis = etree.fromstring(result_thesis, htmlparser)
        not_found = "".join(xDoc_thesis.xpath("/html/body/p[4]/text()"))

        bachelor_thesis = "".join(
            xDoc_thesis.xpath(
                '//li[contains(@class, "breadcrumb-item")][3]//a[text()="bakalářské práce"]/text()'
            )
        )
        master_thesis = "".join(
            xDoc_thesis.xpath(
                '//li[contains(@class, "breadcrumb-item")][3]//a[text()="diplomové práce"]/text()'
            )
        )
        thesis_author_without_degree_surname_first = "".join(
            xDoc_thesis.xpath('//div[./h2/.="Authors"]//div//text()')
        ).strip()
        habilitation_date = "".join(xDoc_thesis.xpath('//div[./h2/.="Date of acceptance"]//div/span/text()'))
        result = "".join(xDoc_thesis.xpath('//div[./h2/.="Result of defence"]//div/span/text()'))
        faculty = "".join(
            xDoc_thesis.xpath(
                '//li[contains(@class, "breadcrumb-item")][4]//a[text()="Fakulta informačních technologií"]/text()'
            )
        )

        if "Page cannot be found" in not_found:
            await inter.edit_original_response(MessagesCZ.thesis_not_found_error)
            return

        habilitation = re.search(r"(\d+)-\d+-\d+", habilitation_date)
        if habilitation is None:
            await inter.edit_original_response(MessagesCZ.thesis_not_found_error)
            return
        habilitation_year = habilitation.group(1)

        thesis_name_split = self._parse_thesis_author(thesis_author_without_degree_surname_first)
        user_full_words = f"{name} {surname}".split()
        if thesis_name_split is not None:
            thesis_given, thesis_surname = thesis_name_split
            author_matches = f"{thesis_given} {thesis_surname}".split() == user_full_words
        else:
            author_matches = thesis_author_without_degree_surname_first.split() in (
                user_full_words,
                f"{surname} {name}".split(),
            )

        if not (
            ((degree == "Ing." and master_thesis != "") or (degree == "Bc." and bachelor_thesis != ""))
            and diploma_year == habilitation_year
            and faculty != ""
            and result == "práce byla úspěšně obhájena"
            and author_matches
        ):
            await inter.edit_original_response(MessagesCZ.web_error)
            self.logger.info(f"[Absolvent] Thesis verification failed for thesis: {thesis_url}")
            self.logger.info("[Absolvent] Data parsed from the website:")
            self.logger.info(f"Degree: {degree}")
            self.logger.info(f"Thesis: {master_thesis} {bachelor_thesis}")
            self.logger.info(f"diploma_year: {diploma_year}")
            self.logger.info(f"habilitation_year: {habilitation_year}")
            self.logger.info(f"faculty: {faculty}")
            self.logger.info(f"result: {result}")
            return

        # DIPLOMA VALIDITY CHECK
        original_msg = await self.append_response(inter, original_msg, MessagesCZ.status_diploma)

        diploma_verified = await self._verify_diploma(diploma_number, name, surname, htmlparser)
        if not diploma_verified and thesis_name_split is not None and thesis_name_split != (name, surname):
            thesis_given, thesis_surname = thesis_name_split
            diploma_verified = await self._verify_diploma(
                diploma_number, thesis_given, thesis_surname, htmlparser
            )

        if not diploma_verified:
            await inter.edit_original_response(MessagesCZ.diploma_error)
            return

        # Add according roles
        original_msg = await self.append_response(inter, original_msg, MessagesCZ.status_roles)

        absolvent_role = None
        if degree == "Bc.":
            absolvent_role = disnake.utils.get(self.base_guild.roles, id=self.config.bc_role_id)
        elif degree == "Ing.":
            absolvent_role = disnake.utils.get(self.base_guild.roles, id=self.config.ing_role_id)
        if absolvent_role:
            for role in author.roles:
                if "ExStudent" in role.name:
                    await author.remove_roles(role, reason="Diploma verification")
                    break
            await author.add_roles(absolvent_role)
            await self.append_response(inter, original_msg, MessagesCZ.diplom_success)

    @staticmethod
    def _parse_thesis_author(thesis_author: str) -> tuple[str, str] | None:
        """Split a DSpace 'Surname, GivenNames' author string into (given_names, surname)."""
        if "," not in thesis_author:
            return None
        thesis_surname, thesis_given = thesis_author.split(",", 1)
        return " ".join(thesis_given.split()), " ".join(thesis_surname.split())

    async def _verify_diploma(
        self,
        diploma_number: str,
        first_name: str,
        last_name: str,
        htmlparser: etree.HTMLParser,
    ) -> bool:
        """Submit the VUT diploma verification form and return whether it succeeded for FIT."""
        diplom_url1 = "https://www.vut.cz/overeni-diplomu"
        diplom_url2 = "https://www.vut.cz/overeni-diplomu?aid_redir=1"
        diplom_url3 = "https://www.vut.cz/overeni-diplomu"
        data = {}

        try:
            # load initial cookies + download the HTML-security codes in hidden input fields
            await self.bot.rubbergod_session.get(diplom_url1)
            async with self.bot.rubbergod_session.get(diplom_url2) as response:
                result2 = await response.text()
        except (aiohttp.ClientConnectorError, asyncio.TimeoutError) as error:
            raise ApiError(str(error))

        xDoc2 = etree.fromstring(result2, htmlparser)
        inputs = xDoc2.xpath("//*[@id='over_studenta']/input[@type='hidden']")
        for hidden_input in inputs:
            data[hidden_input.attrib["name"]] = hidden_input.attrib["value"]

        data["data[form_el_cislo]"] = diploma_number
        data["data[form_el_jmeno]"] = first_name
        data["data[form_el_prijmeni]"] = last_name
        data["data[form_el_overit]"] = "Ověřit"

        async with self.bot.rubbergod_session.post(diplom_url3, data=data) as response:
            result3 = await response.text()
        xDoc3 = etree.fromstring(result3, htmlparser)
        absolvent_text = "".join(
            xDoc3.xpath(
                "//*[@id='main']/div[contains(@class,'alert-success')]/div[@class='alert-text']/div//text()"
            )
        )
        return (
            absolvent_text != ""
            and "úspěšně ověřen" in absolvent_text
            and absolvent_text.endswith(", Fakulta informačních technologií")
        )

    async def append_response(self, inter: disnake.ApplicationCommandInteraction, old: str, new: str) -> str:
        """Append new string to the original message and send"""
        if old:
            # remove loading emoji, add checkmark
            old = old.rsplit("<", 1)[0] + "✅"
        msg = f"{old}\n{new}"
        await inter.edit_original_response(msg)
        return msg

    @diplom.error
    async def diplom_error(self, inter: disnake.ApplicationCommandInteraction, error):
        await inter.edit_original_response(MessagesCZ.diplom_help_print(user=inter.author.id))
