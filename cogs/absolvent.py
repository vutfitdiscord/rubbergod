import discord
from discord.ext import commands

import unicodedata
import requests
from lxml import etree
import re

from repository import user_repo
from config.app_config import Config
from config.messages import Messages

user_r = user_repo.UserRepository()


class Absolvent(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def diplom(self, ctx, degree, name, surname, diploma_number, thesis_web_id):
        """Command for diploma verification and honourable role addition

        :param ctx: discord context
        :param name: first name (case-sensitive)
        :param surname: last name (case-sensitive)
        :param degree: strictly either "Bc." or "Ing." (case-sensitive)
        :param diploma_number: ID of diploma, in format NNNNNN/YYYY
        :param thesis_web_id: ID from URL https://www.vutbr.cz/studenti/zav-prace?zp_id=<num>
        """
        # prepare
        htmlparser = etree.HTMLParser()
        full_name_with_degree = f"{degree} {name} {surname}"
        full_name_without_degree = f"{name} {surname}"
        diploma_year = re.search(r"\d+/(\d+)", diploma_number).group(1)
        guild = self.bot.get_guild(Config.guild_id)

        # CHECK WHETHER THE PROVIDED NAME MATCHES THE ONE STORED FOR FIT VUT VERIFICATION

        def remove_accents(input_str):
            nfkd_form = unicodedata.normalize("NFKD", input_str)
            only_ascii = nfkd_form.encode("ASCII", "ignore").decode("ASCII")
            return only_ascii

        # get "surname name" for bot database fot the current command caller
        name_from_db = user_r.get_user_by_id(ctx.author.id).name
        # remove diacritics from the user-supplied name
        name_from_user_without_diacritics = remove_accents(f"{surname} {name}")

        if name_from_db != name_from_user_without_diacritics:
            await ctx.send(Messages.absolvent_wrong_name)
            return

        # CHECK OWNERSHIP, TYPE AND YEAR OF THE QUALIFICATION WORK / THESIS

        thesis_url = f"https://www.vutbr.cz/studenti/zav-prace?zp_id={thesis_web_id}"

        # download the page
        result_thesis = requests.get(thesis_url)
        # parse it using lxml
        xDoc_thesis = etree.fromstring(result_thesis.text, htmlparser)
        master_thesis = "".join(
            xDoc_thesis.xpath("//*[@id='main']//span[contains(@class,'tag') and .='diplomová práce']/text()")
        )
        bachelor_thesis = "".join(
            xDoc_thesis.xpath("//*[@id='main']//span[contains(@class,'tag') and .='bakalářská práce']/text()")
        )
        thesis_author = "".join(
            xDoc_thesis.xpath(
                "//*[@id='main']//p[contains(@class,'b-detail__annot')]/span[starts-with(.,'Autor práce')]/*[self::a or self::strong]/text()"
            )
        )
        habilitation_date = "".join(
            xDoc_thesis.xpath(
                "//*[@id='main']//div[contains(@class,'b-detail__body')]//div[p='Termín obhajoby']/following-sibling::div[1]//text()"
            )
        )
        result = "".join(
            xDoc_thesis.xpath(
                "//*[@id='main']//div[contains(@class,'b-detail__body')]//div[p='Výsledek obhajoby']/following-sibling::div[1]//text()"
            )
        )
        faculty = "".join(
            xDoc_thesis.xpath(
                "//*[@id='main']//div[contains(@class,'b-detail__body')]//div[p='Fakulta']/following-sibling::div[1]//text()"
            )
        )

        habilitation_year = re.search(r"\d+\.\s*\d+\.\s*(\d+)", habilitation_date).group(1)
        thesis_author_without_degree = re.search(r"(\w+\. +)?([\w ]+)", thesis_author).group(2)

        if not (
            ((degree == "Ing." and master_thesis != "") or (degree == "Bc." and bachelor_thesis != ""))
            and diploma_year == habilitation_year
            and faculty == "Fakulta informačních technologií"
            and result == "obhájeno (práce byla úspěšně obhájena)"
            and thesis_author_without_degree == full_name_without_degree
        ):
            await ctx.send(Messages.absolvent_web_error)
            return

        # DIPLOMA VALIDITY CHECK

        diplom_url1 = "https://www.vutbr.cz/overeni-diplomu"
        diplom_url2 = "https://www.vutbr.cz/overeni-diplomu?aid_redir=1"
        diplom_url3 = "https://www.vutbr.cz/overeni-diplomu"
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
            await ctx.send(Messages.absolvent_web_error)
            return

        guild = self.bot.get_guild(Config.guild_id)
        role = None
        if degree == "Bc.":
            role = discord.utils.get(guild.roles, id=Config.bc_role_id)
        if degree == "Ing.":
            role = discord.utils.get(guild.roles, id=Config.ing_role_id)
        if role:
            member = guild.get_member(ctx.author.id)
            await member.add_roles(role)
            await ctx.send(Messages.absolvent_success)

    @diplom.error
    async def diplom_error(self, ctx, error):
        await ctx.send(Messages.absolvent_help)


def setup(bot):
    bot.add_cog(Absolvent(bot))
