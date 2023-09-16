from datetime import datetime, time
from enum import Enum
from statistics import mean
from typing import Union

import disnake
import requests
from bs4 import BeautifulSoup

import utils
from config.app_config import config
from config.messages import Messages
from database.review import (ProgrammeDB, ReviewDB, ReviewRelevanceDB,
                             SubjectDB, SubjectDetailsDB)
from features import sports


class TierEnum(Enum):
    """Tier to grades mapping"""
    A = 0  # 1
    B = 1  # 1.5
    C = 2  # 2
    D = 3  # 2.5
    E = 4  # 3
    # skip 5 as there is no 3.5 grade
    F = 6  # 4

    def tier_to_grade_num(tier: int) -> int:
        return 1 + tier/2


class ReviewManager:
    """Helper class for reviews"""

    def __init__(self, bot):
        self.bot = bot

    def make_embed(
        self,
        msg_author: disnake.User,
        review: ReviewDB,
        subject: Union[SubjectDetailsDB, str],
        description: str,
        page: str
    ):
        """Create new embed for reviews"""
        if type(subject) == SubjectDetailsDB:
            shortcut = getattr(subject, "shortcut")
        else:
            shortcut = subject
        embed = disnake.Embed(title=f"{shortcut} reviews", description=description)
        embed.color = 0x6D6A69
        id = 0
        if review:
            id = review.id
            if review.anonym:
                author = "Anonym"
            else:
                guild = self.bot.get_guild(config.guild_id)
                author = guild.get_member(int(review.member_ID))
            embed.add_field(name=Messages.review_author_label, value=author)
            embed.add_field(name=Messages.review_grade_label, value=TierEnum(review.tier).name)
            embed.add_field(
                name=Messages.review_date_label,
                value=utils.get_discord_timestamp(datetime.combine(review.date, time(12, 0)), "Relative Time")
            )
            text = review.text_review
            if text is not None:
                if len(text) > 1024:
                    pages = utils.cut_string_by_words(text, 1000, " ")
                    text = pages[0]
                    embed.add_field(
                        name=Messages.review_text_page_label,
                        value=f"1/{len(pages)}",
                        inline=False
                    )
                embed.add_field(name=Messages.review_text_label, value=text, inline=False)
            likes = ReviewRelevanceDB.get_votes_count(review.id, True)
            embed.add_field(name="👍", value=f"{likes}")
            dislikes = ReviewRelevanceDB.get_votes_count(review.id, False)
            embed.add_field(name="👎", value=f"{dislikes}")
            diff = likes - dislikes
            if diff > 0:
                embed.color = 0x34CB0B
            elif diff < 0:
                embed.color = 0xCB410B
        if type(subject) == SubjectDetailsDB and not subject.shortcut.lower().startswith("tv"):
            sem = 1 if subject.semester == "L" else 2
            subject_id = subject.card.split("/")[-2]
            vutis_link = "https://www.vut.cz/studis/student.phtml?script_name=anketa_statistiky"
            embed.add_field(
                name=Messages.review_other_reviews_label,
                value=f"[VUT IS]({vutis_link}&apid={subject_id}&typ_semestru_id={sem})",
                inline=False,
            )
        utils.add_author_footer(embed, msg_author, additional_text=[f"Review: {page} | ID: {id}"])
        return embed

    def update_embed(self, embed: disnake.Embed, review: ReviewDB, text_page: int = 1):
        """Update embed fields"""
        embed.color = 0x6D6A69
        text = review.text_review
        idx = 3
        add_new_field = False
        fields_cnt = len(embed.fields)
        if text is not None:
            if len(text) > 1024:
                pages = utils.cut_string_by_words(text, 1000, " ")
                text = pages[text_page - 1]
                embed.set_field_at(
                    idx,
                    name=Messages.review_text_page_label,
                    value=f"{text_page}/{len(pages)}",
                    inline=False
                )
                idx += 1
            embed.set_field_at(idx, name=Messages.review_text_label, value=text, inline=False)
            idx += 1
        likes = ReviewRelevanceDB.get_votes_count(review.id, True)
        embed.set_field_at(idx, name="👍", value=f"{likes}")
        dislikes = ReviewRelevanceDB.get_votes_count(review.id, False)
        idx += 1
        if add_new_field or fields_cnt <= idx:
            embed.add_field(name="👎", value=f"{dislikes}")
            add_new_field = True
        else:
            embed.set_field_at(idx, name="👎", value=f"{dislikes}")
        idx += 1
        if not review.subject.lower().startswith("tv"):
            # don't remove IS link field on fit courses
            idx += 1
        for _ in range(fields_cnt - idx):
            embed.remove_field(idx)
        diff = likes - dislikes
        if diff > 0:
            embed.color = 0x34CB0B
        elif diff < 0:
            embed.color = 0xCB410B
        return embed

    def add_review(self, author_id: int, subject: str, tier: int, anonym: bool, text: str):
        """Add new review, if review with same author and subject exists -> update"""
        if not SubjectDB.get(subject):
            return False
        review = ReviewDB.get_review_by_author_subject(author_id, subject)
        if review:
            review.tier = tier
            review.anonym = anonym
            review.text_review = text
            review.update()
        else:
            ReviewDB.add_review(author_id, subject, tier, anonym, text)
        return True

    def list_reviews(self, author: disnake.User, subject: str):
        subject_obj = SubjectDB.get(subject)
        if not subject_obj:
            subject_obj = SubjectDB.get(f"tv-{subject}")
            if not subject_obj:
                return None
        reviews = ReviewDB.get_subject_reviews(subject_obj.shortcut)
        reviews_cnt = len(reviews)
        subject_details = SubjectDetailsDB.get(subject_obj.shortcut) or subject_obj.shortcut
        name = getattr(subject_details, "name",  "")
        if reviews_cnt == 0:
            description = f"{name}\n{Messages.review_embed_no_reviews}"
            return [self.make_embed(author, None, subject_details, description, "1/1")]
        else:
            embeds = []
            avg_tier = mean([review.ReviewDB.tier for review in reviews])
            for idx in range(reviews_cnt):
                review = reviews[idx].ReviewDB
                grade_num = TierEnum.tier_to_grade_num(avg_tier)
                grade = f"{TierEnum(round(avg_tier)).name}({round(grade_num, 1)})"
                description = Messages.review_embed_description(name=name, grade=grade)
                page = f"{idx+1}/{reviews_cnt}"

                embeds.append(self.make_embed(author, review, subject_details, description, page))
            return embeds

    def remove(self, author: str, subject: str):
        """Remove review from DB"""
        result = ReviewDB.get_review_by_author_subject(author, subject)
        if result:
            result.remove()
            return True
        else:
            return False

    def authored_reviews(self, author: str):
        """Returns embed of reviews written by user"""
        reviews = ReviewDB.get_reviews_by_author(author)
        reviews_cnt = reviews.count()

        if reviews_cnt == 0:
            description = Messages.review_embed_no_reviews
        else:
            description = '\n'.join(map(lambda x: x.subject.upper(), reviews))

        embed = disnake.Embed(title=Messages.review_authored_list_label, description=description)
        return embed

    def add_vote(self, review_id: int, vote: bool, author: str):
        """Add/update vote for review"""
        relevance = ReviewRelevanceDB.get_vote_by_author(review_id, author)
        if not relevance or relevance.vote != vote:
            ReviewRelevanceDB.add_vote(review_id, vote, author)

    def update_subject_types(self, link: str, MIT: bool, overwrite: bool = False):
        """Send request to `link`, parse page and find all subjects.
        Add new subjects to DB, if subject already exists update its years.
        For MITAI links please set `MIT` to True.
        If update succeeded return True, otherwise False
        """
        degree = "MIT" if MIT else "BIT"

        response = requests.get(link)
        if response.status_code != 200:
            return False
        soup = BeautifulSoup(response.content, "html.parser")
        tables = soup.select("table")

        # remove last table with information about PVT and PVA subjects (applicable mainly for BIT)
        if len(tables) % 2:
            tables = tables[:-1]

        # specialization shortcut for correct year definition in DB
        specialization = soup.select("main p strong")[0].get_text()
        full_specialization = soup.select("h1")[0].get_text()

        programmme_db = ProgrammeDB.get(specialization)
        if not programmme_db or programmme_db.link != link:
            ProgrammeDB.set(specialization, full_specialization, link)

        for table in tables:
            header = table.select("h4")  # e.g. '1. ročník, zimní semestr' or 'libovolný ročník, ...'
            if not header:
                # other table
                continue
            header = header[0].get_text().split(',')
            year = header[0].strip()[0].upper()
            if year != 'L':
                year = int(year)
            sem = header[1].strip()[0].upper()
            rows = table.select("tbody tr")
            for row in rows:
                shortcut = row.find_all("th")[0].get_text()
                # not a subject table
                columns = row.find_all("td")
                if len(columns) != 5:
                    continue
                # update subject DB
                if not SubjectDB.get(shortcut.lower()):
                    SubjectDB.add(shortcut.lower())
                name = columns[0].get_text()
                credit = columns[1].get_text()
                type = columns[2].get_text()
                for_year = "VMIT" if MIT else "VBIT"
                if type == "P":
                    for_year = f"{year}{specialization}"
                detail = SubjectDetailsDB.get(shortcut)
                if not detail or overwrite:
                    # subject not in DB or overwrite requested
                    SubjectDetailsDB(
                        shortcut=shortcut,
                        name=name,
                        credits=credit,
                        semester=sem,
                        end=columns[3].get_text(),
                        card=columns[0].find("a").attrs["href"],
                        type=type,
                        year=for_year,
                        degree=degree,
                    ).update()
                else:
                    changed = False
                    if name != detail.name:
                        # Update name mainly for courses that are not opened
                        detail.name = name
                        changed = True
                    if credit != detail.credits:
                        detail.credits = credit
                        changed = True
                    if for_year not in detail.year.split(", "):
                        # subject already in DB with different year (applicable mainly for MIT)
                        if type not in detail.type.split(", "):
                            detail.type += f", {type}"
                        if detail.year:
                            detail.year += f", {for_year}"
                        changed = True
                    if sem not in detail.semester.split(", "):
                        # subject already in DB with different semester (e.g. RET)
                        detail.semester += f", {sem}"
                        changed = True
                    if degree not in detail.degree.split(", "):
                        # subject already in DB with different degree (e.g. RET)
                        detail.degree += f", {degree}"
                        changed = True
                    if detail.card != columns[0].find("a").attrs["href"]:
                        # ID was updated
                        detail.card = columns[0].find("a").attrs["href"]
                        changed = True
                    if changed:
                        detail.update()
        return True

    def update_sport_subjects(self):
        sports_list = sports.VutSports().get_sports()
        for item in sports_list:
            if not SubjectDB.get(item.shortcut.lower()):
                SubjectDB.add(item.shortcut.lower())
                SubjectDetailsDB(
                    shortcut=item.shortcut,
                    name=item.name,
                    credits=1,
                    semester=item.semester.value,
                    end="Za",
                    card=item.subject_id,
                    type="V",
                    year="VBIT, VMIT",
                    degree="BIT, MIT",
                ).update()
