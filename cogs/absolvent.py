"""
Cog for diploma verification. When successful, the user is given Survivor(Bc.) or King(Ing.) role.
"""

import re
import unicodedata

import disnake
import requests
from disnake.ext import commands
from lxml import etree

from cogs.base import Base
from config.messages import Messages
from database.verification import ValidPersonDB


class Absolvent(Base, commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @commands.slash_command(name="diplom_help", description=Messages.absolvent_help_brief)
    async def diplom_help(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.send_message(Messages.absolvent_help)

    @commands.slash_command(name="diplom", description=Messages.absolvent_brief)
    async def diplom(
        self,
        inter: disnake.ApplicationCommandInteraction,
        degree: str = commands.Param(choices=["Bc.", "Ing."], description=Messages.absolvent_degree_param),
        name: str = commands.Param(description=Messages.absolvent_name_param),
        surname: str = commands.Param(description=Messages.absolvent_surname_param),
        diploma_number: str = commands.Param(description=Messages.absolvent_diploma_param),
        thesis_web_id: int = commands.Param(description=Messages.absolvent_thesis_id_param)
    ):
        """Command for diploma verification and honourable role addition

        :param inter: disnake interaction
        :param name: first name (case-sensitive)
        :param surname: last name (case-sensitive)
        :param degree: strictly either "Bc." or "Ing." (case-sensitive)
        :param diploma_number: ID of diploma, in format NNNNNN/YYYY
        :param thesis_web_id: ID from URL https://dspace.vutbr.cz/handle/11012/<num>
            can be discovered via https://dspace.vutbr.cz/handle/11012/19121
        """
        await inter.response.defer(with_message=True, ephemeral=True)

        # check whether the user is verified
        verify_role = inter.guild.get_role(self.config.verification_role_id)
        if verify_role not in inter.author.roles:
            await inter.edit_original_response(Messages.absolvent_not_verified)
            return

        if thesis_web_id == "19121":
            await inter.edit_original_response(Messages.absolvent_id_from_help)
            return

        # prepare
        htmlparser = etree.HTMLParser()
        diploma_year = re.search(r"\d+/(\d+)", diploma_number)
        if not diploma_year:
            await inter.edit_original_response(Messages.absolvent_wrong_diploma_format)
            return
        diploma_year = diploma_year.group(1)
        full_name_without_degree_surname_first = f"{surname}, {name}"

        # CHECK WHETHER THE PROVIDED NAME MATCHES THE ONE STORED FOR FIT VUT VERIFICATION

        def remove_accents(input_str):
            nfkd_form = unicodedata.normalize("NFKD", input_str)
            only_ascii = nfkd_form.encode("ASCII", "ignore").decode("ASCII")
            return only_ascii

        # get "surname name" for bot database fot the current command caller
        name_from_db = ValidPersonDB.get_user_by_id(inter.author.id).name
        # remove diacritics from the user-supplied name
        name_from_user_without_diacritics = remove_accents(f"{surname} {name}")

        if name_from_db is None:
            await inter.edit_original_response(Messages.absolvent_not_in_db)
            return

        if name_from_db != name_from_user_without_diacritics:
            await inter.edit_original_response(Messages.absolvent_wrong_name)
            return

        # CHECK OWNERSHIP, TYPE AND YEAR OF THE QUALIFICATION WORK / THESIS

        thesis_url = f"https://dspace.vutbr.cz/handle/11012/{thesis_web_id}?locale-attribute=cs"

        # download the page
        result_thesis = requests.get(thesis_url)
        # parse it using lxml
        xDoc_thesis = etree.fromstring(result_thesis.text, htmlparser)
        not_found = "".join(
            xDoc_thesis.xpath('//*[@id="main-container"]//h2/text()')
        )
        master_thesis = "".join(
            xDoc_thesis.xpath(
               "/html/body/div[1]/div/div/div/ul[contains(@class,'breadcrumb')]"
               "/li[3]/a[.='diplomové práce']/text()"
            )
        )
        bachelor_thesis = "".join(
            xDoc_thesis.xpath(
               "/html/body/div[1]/div/div/div/ul[contains(@class,'breadcrumb')]"
               "/li[3]/a[.='bakalářské práce']/text()"
            )
        )
        thesis_author_without_degree_surname_first = "".join(
            xDoc_thesis.xpath(
                '//*[@id="aspect_artifactbrowser_ItemViewer_div_item-view"]'
                '/div/div[2]/div[1]/div[./h5/b="Autor"]/div/a/text()'
            )
        )
        habilitation_date = "".join(
            xDoc_thesis.xpath(
                '//*[@id="aspect_artifactbrowser_ItemViewer_div_item-view"]'
                '/div/div[2]/div[2]/div[./h5="Termín obhajoby"]/span/text()'
            )
        )
        result = "".join(
            xDoc_thesis.xpath(
                '//*[@id="aspect_artifactbrowser_ItemViewer_div_item-view"]'
                '/div/div[2]/div[2]/div[./h5="Výsledek obhajoby"]/span/text()'
            )
        )
        faculty = "".join(
            xDoc_thesis.xpath(
               "/html/body/div[1]/div/div/div/ul[contains(@class,'breadcrumb')]/"
               "li[4]/a[.='Fakulta informačních technologií']/text()"
            )
        )

        if "Page cannot be found" in not_found:
            await inter.edit_original_response(Messages.absolvent_thesis_not_found_error)
            return

        habilitation_year = re.search(r"(\d+)-\d+-\d+", habilitation_date)
        if habilitation_year is None:
            await inter.edit_original_response(Messages.absolvent_thesis_not_found_error)
            return
        habilitation_year = habilitation_year.group(1)

        if not (
            ((degree == "Ing." and master_thesis != "") or (degree == "Bc." and bachelor_thesis != ""))
            and diploma_year == habilitation_year
            and faculty != ""
            and result == "práce byla úspěšně obhájena"
            and thesis_author_without_degree_surname_first == full_name_without_degree_surname_first
        ):
            await inter.edit_original_response(Messages.absolvent_web_error)
            return

        # DIPLOMA VALIDITY CHECK

        diplom_url1 = "https://www.vut.cz/overeni-diplomu"
        diplom_url2 = "https://www.vut.cz/overeni-diplomu?aid_redir=1"
        diplom_url3 = "https://www.vut.cz/overeni-diplomu"
        data = {}
        session = requests.session()

        # load initial cookies + download the HTML-security codes in hidden input fields
        session.get(diplom_url1)
        result2 = session.get(diplom_url2)
        # parse it using lxml
        xDoc2 = etree.fromstring(result2.text, htmlparser)
        # get all hidden server-generated inputs
        inputs = xDoc2.xpath("//*[@id='over_studenta']/input[@type='hidden']")
        for input in inputs:
            data[input.attrib["name"]] = input.attrib["value"]

        # add user-supplied values
        data["data[form_el_cislo]"] = diploma_number
        data["data[form_el_jmeno]"] = name
        data["data[form_el_prijmeni]"] = surname
        data["data[form_el_overit]"] = "Ověřit"

        # send the POST to check the diploma validity
        result3 = session.post(diplom_url3, data)
        xDoc3 = etree.fromstring(result3.text, htmlparser)
        # parse the success text (in czech)
        absolventText = "".join(
            xDoc3.xpath(
                "//*[@id='main']/div[contains(@class,'alert-success')]/div[@class='alert-text']/div//text()"
            )
        )
        if not (
            absolventText != ""
            and "úspěšně ověřen" in absolventText
            and absolventText.endswith(", Fakulta informačních technologií")
        ):
            await inter.edit_original_response(Messages.absolvent_diploma_error)
            return

        guild = self.bot.get_guild(self.config.guild_id)
        role = None
        if degree == "Bc.":
            role = disnake.utils.get(guild.roles, id=self.config.bc_role_id)
        if degree == "Ing.":
            role = disnake.utils.get(guild.roles, id=self.config.ing_role_id)
        if role:
            member = guild.get_member(inter.author.id)
            for drop_role in member.roles:
                if "Dropout" in drop_role.name:
                    await member.remove_roles(drop_role, reason="Diploma verification")
            await member.add_roles(role)
            await inter.edit_original_response(Messages.absolvent_success)

    @diplom.error
    async def diplom_error(self, inter: disnake.ApplicationCommandInteraction, error):
        await inter.edit_original_response(
            Messages.absolvent_help(user=inter.author.id)
        )


def setup(bot):
    bot.add_cog(Absolvent(bot))
