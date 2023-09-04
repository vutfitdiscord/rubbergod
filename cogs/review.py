"""
Cog implementing review system for subjects.
"""

import copy
import datetime

import disnake
from disnake.ext import commands

import utils
from buttons.embed import EmbedView
from buttons.review import ReviewView
from cogs.base import Base
from config import cooldowns
from config.messages import Messages
from database.review import ProgrammeDB, ReviewDB, SubjectDB, SubjectDetailsDB
from features.review import ReviewManager, TierEnum
from permissions import permission_check

subjects = []
programmes = []
subjects_programmes = []


async def autocomp_subjects_programmes(inter: disnake.ApplicationCommandInteraction, user_input: str):
    return [item for item in subjects_programmes if user_input.lower() in item][:25]


async def autocomp_subjects(inter: disnake.ApplicationCommandInteraction, user_input: str):
    return [subject for subject in subjects if user_input.lower() in subject][:25]


class Review(Base, commands.Cog):
    def __init__(self, bot: commands.Bot):
        global subjects, programmes
        super().__init__()
        self.bot = bot
        self.manager = ReviewManager(bot)
        subjects = SubjectDB.get_all()
        programmes = ProgrammeDB.get_all()
        self.get_all_options()

    def get_all_options(self):
        global subjects, programmes, subjects_programmes
        subjects = [subject[0] for subject in subjects]
        programmes = [programme[0] for programme in programmes]
        programmes = [programme.lower() for programme in programmes]
        subjects_programmes = subjects + programmes
        subjects_programmes.sort()

    async def check_member(self, inter: disnake.ApplicationCommandInteraction):
        """Check if user is allowed to add/remove new review."""
        guild = inter.bot.get_guild(self.config.guild_id)
        member = guild.get_member(inter.author.id)
        if member is None:
            await inter.send(Messages.review_not_on_server(user=inter.author.mention))
            return False
        roles = member.roles
        verify = False
        for role in roles:
            if self.config.verification_role_id == role.id:
                verify = True
            if role.id in self.config.review_forbidden_roles:
                await inter.send(Messages.review_add_denied(user=inter.author.id))
                return False
        if not verify:
            await inter.send(Messages.review_add_denied(user=inter.author.id))
            return False
        return True

    @cooldowns.short_cooldown
    @commands.slash_command(name="review")
    async def reviews(self, inter: disnake.ApplicationCommandInteraction):
        """Group of commands for reviews."""
        pass

    @reviews.sub_command(name="get", description=Messages.review_get_brief)
    async def get(
        self,
        inter: disnake.ApplicationCommandInteraction,
        subject: str = commands.Param(autocomplete=autocomp_subjects),
    ):
        """Get reviews"""
        await inter.response.defer()
        embeds = self.manager.list_reviews(inter.author, subject.lower())
        if embeds is None or len(embeds) == 0:
            await inter.send(Messages.review_wrong_subject)
            return
        view = ReviewView(inter.author, self.bot, embeds)
        await inter.edit_original_response(embed=embeds[0], view=view)
        view.message = await inter.original_message()

    @reviews.sub_command(name="add", description=Messages.review_add_brief)
    async def add(
        self,
        inter: disnake.ApplicationCommandInteraction,
        subject: str = commands.Param(autocomplete=autocomp_subjects),
        grade: str = commands.Param(choices=TierEnum._member_names_, description=Messages.review_grade_brief),
        text: str = commands.Param(),
        anonymous: bool = commands.Param(default=False)
    ):
        """Add new review for `subject`"""
        # TODO: use modal in future when select in modal support release
        # await inter.response.send_modal(modal=ReviewModal(self.bot))
        await inter.response.defer(ephemeral=anonymous)
        tier = getattr(TierEnum, grade).value
        if not await self.check_member(inter):
            return
        if not self.manager.add_review(inter.author.id, subject.lower(), tier, anonymous, text):
            await inter.send(Messages.review_wrong_subject)
        else:
            await inter.send(Messages.review_added)

    @reviews.sub_command(name="remove", description=Messages.review_remove_brief)
    async def remove(
        self,
        inter: disnake.ApplicationCommandInteraction,
        subject: str = None,
        id: int = commands.Param(default=None, description=Messages.review_id_brief)
    ):
        """Remove review from DB. User is just allowed to remove his own review
        For admin it is possible to use "id" as subject shortcut and delete review by its ID
        """
        await inter.response.defer()
        if id is not None:
            if permission_check.is_bot_admin(inter, False):
                review = ReviewDB.get_review_by_id(id)
                if review:
                    review.remove()
                    await inter.send(Messages.review_remove_success)
                else:
                    await inter.send(Messages.review_not_found)
                return

            # not admin
            await inter.send(
                Messages.review_remove_denied(user=inter.author.id),
                ephemeral=True
            )
            return
        elif subject is not None:
            subject = subject.lower()
            if self.manager.remove(str(inter.author.id), subject):
                await inter.send(Messages.review_remove_success)
                return
        await inter.send(Messages.review_not_found)

    @reviews.sub_command(name="list", description=Messages.review_list_brief)
    async def author_list(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        embed = self.manager.authored_reviews(inter.author.id)
        await inter.send(embed=embed)

    @cooldowns.short_cooldown
    @commands.slash_command(name="subject")
    @commands.check(permission_check.is_bot_admin)
    async def subject(self, inter: disnake.ApplicationCommandInteraction):
        """Group of commands for managing subjects in DB"""
        await inter.response.defer()

    @subject.sub_command(name="update", description=Messages.subject_update_biref)
    async def update(
        self,
        inter: disnake.ApplicationCommandInteraction,
        overwrite: bool = commands.Param(description=Messages.subject_update_overwrite_brief, default=False),
    ):
        """Updates subjects from web"""
        global subjects, programmes
        programme_details_link = "https://www.fit.vut.cz/study/"
        reply = ""
        # bachelor
        url = f"{programme_details_link}program/{self.config.subject_bit_id}/.cs"
        if not self.manager.update_subject_types(url, False, overwrite):
            reply += Messages.subject_update_error(url=url)
        # engineer
        ids_list = list(range(self.config.subject_mit_id_start, self.config.subject_mit_id_end))
        for id in ids_list + self.config.subject_mit_id_rnd:
            url = f"{programme_details_link}field/{id}/.cs"
            if not self.manager.update_subject_types(url, True, overwrite):
                reply += Messages.subject_update_error(url=url)
        # sports
        self.manager.update_sport_subjects()
        subjects = SubjectDB.get_all()
        programmes = ProgrammeDB.get_all()
        self.get_all_options()
        reply += Messages.subject_update_success
        await inter.edit_original_response(reply)

    @commands.slash_command(name="wtf", description=Messages.shortcut_brief)
    async def shortcut(
        self,
        inter: disnake.ApplicationCommandInteraction,
        shortcut: str = commands.Param(autocomplete=autocomp_subjects_programmes),
    ):
        """Informations about subject specified by its shortcut"""
        programme = ProgrammeDB.get(shortcut.upper())
        if programme:
            embed = disnake.Embed(title=programme.shortcut, description=programme.name)
            embed.add_field(name="Link", value=programme.link)
        else:
            subject = SubjectDetailsDB.get(shortcut)
            if not subject:
                subject = SubjectDetailsDB.get(f"TV-{shortcut}")
                if not subject:
                    await inter.response.send_message(Messages.review_wrong_subject)
                    return
            embed = disnake.Embed(title=subject.shortcut, description=subject.name)
            if subject.semester == "L":
                semester_value = "Letní"
            elif subject.semester == "Z":
                semester_value = "Zimní"
            else:
                semester_value = "Zimní, Letní"
            embed.add_field(name="Semestr", value=semester_value)
            embed.add_field(name="Typ", value=subject.type)
            if subject.year:
                embed.add_field(name="Ročník", value=subject.year)
            embed.add_field(name="Kredity", value=subject.credits)
            embed.add_field(name="Ukončení", value=subject.end)
            if "*" in subject.name:
                embed.add_field(name="Upozornění", value="Předmět není v tomto roce otevřen", inline=False)
            if subject.shortcut.startswith("TV-"):
                embed.add_field(
                    name="Rozvrh předmětu v IS",
                    value="https://www.vut.cz/studis/student.phtml?sn=rozvrhy&action=gm_rozvrh_predmetu"
                    f"&operation=rozvrh&predmet_id={subject.card}&fakulta_id=814",
                    inline=False
                )
            else:
                embed.add_field(
                    name="Karta předmětu",
                    value=f"https://www.fit.vut.cz/study/course/{subject.shortcut}/.cs",
                    inline=False
                )
                embed.add_field(
                    name="Statistika úspěšnosti předmětu",
                    value=f"http://fit.nechutny.net/?detail={subject.shortcut}",
                    inline=False,
                )

        utils.add_author_footer(embed, inter.author)
        await inter.response.send_message(embed=embed)

    @commands.slash_command(name="tierboard", description=Messages.tierboard_brief)
    async def tierboard(
        self,
        inter: disnake.ApplicationCommandInteraction,
        type: str = commands.Param(name="typ", choices=["P", "PVT", "PVA", "V"]),
        sem: str = commands.Param(name="semestr", choices=["Z", "L"]),
        year: str = commands.Param(
            name="rocnik", choices=["1BIT", "2BIT", "3BIT", "1MIT", "2MIT"], default=""
        )
    ):
        """Board of suject based on average tier from reviews"""
        degree = None

        author = inter.author
        if not inter.guild:  # DM
            guild = self.bot.get_guild(self.config.guild_id)
            author = guild.get_member(author.id)
        if not year:
            for role in author.roles:
                if any(deg in role.name for deg in ["BIT", "MIT"]):
                    if role.name == "0BIT":
                        year = "1BIT"
                    elif role.name == "0MIT":
                        year = "1MIT"
                    else:
                        year = role.name
                    break
        if "BIT" in year:
            degree = "BIT"
        if "MIT" in year:
            degree = "MIT"
        if not degree and not year:
            await inter.send(Messages.tierboard_missing_year, ephemeral=True)
            return
        embeds = []
        embed = disnake.Embed(title="Tierboard")
        embed.timestamp = datetime.datetime.now(tz=datetime.timezone.utc)
        embed.add_field(name="Typ", value=type)
        embed.add_field(name="Semestr", value="Letní" if sem == "L" else "Zimní")
        if type != "P":
            embed.add_field(name="Program", value=degree)
            year = ""
        else:
            embed.add_field(name="Ročník", value=year)
        utils.add_author_footer(embed, author)

        pages_total = SubjectDetailsDB.get_tierboard_page_count(type, sem, degree, year)
        for page in range(pages_total):
            board = SubjectDetailsDB.get_tierboard(type, sem, degree, year, page*10)
            output = ""
            cnt = 1
            for line in board:
                # grade format: "B (1.7)"
                grade_num = TierEnum.tier_to_grade_num(line.avg_tier)
                grade = f"{TierEnum(round(line.avg_tier)).name}({round(grade_num, 1)})"
                output += f"{cnt} - **{line.shortcut}**: {grade}\n"
                cnt += 1
            embed.description = output
            embeds.append(copy.copy(embed))

        if pages_total == 0:
            embed.description = ""
            embeds.append(embed)

        view = EmbedView(inter.author, embeds)
        await inter.response.send_message(embed=embeds[0], view=view)
        view.message = await inter.original_message()


def setup(bot: commands.Bot):
    bot.add_cog(Review(bot))
