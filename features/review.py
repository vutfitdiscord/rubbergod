from bs4 import BeautifulSoup
import disnake
import requests

from repository import review_repo
from features import sports
from config.app_config import config
from repository.database.review import Review, Subject_details
import utils


class ReviewManager:
    """Helper class for reviews"""

    def __init__(self, bot):
        self.bot = bot
        self.repo = review_repo.ReviewRepository()

    def make_embed(
        self,
        msg_author: disnake.User,
        review: Review,
        subject: Subject_details,
        description: str,
        page: str
    ):
        """Create new embed for reviews"""
        embed = disnake.Embed(title=f"{subject.shortcut.upper()} reviews", description=description)
        embed.colour = 0x6D6A69
        id = 0
        if review:
            id = review.id
            if review.anonym:
                author = "Anonym"
            else:
                guild = self.bot.get_guild(config.guild_id)
                author = guild.get_member(int(review.member_ID))
            embed.add_field(name="Author", value=author)
            embed.add_field(name="Tier", value=review.tier)
            embed.add_field(name="Date", value=review.date)
            text = review.text_review
            if text is not None:
                text_len = len(text)
                if text_len > 1024:
                    pages = text_len // 1024 + (text_len % 1024 > 0)
                    text = text[:1024]
                    embed.add_field(name="Text page", value=f"1/{pages}", inline=False)
                embed.add_field(name="Text", value=text, inline=False)
            likes = self.repo.get_votes_count(review.id, True)
            embed.add_field(name="👍", value=f"{likes}")
            dislikes = self.repo.get_votes_count(review.id, False)
            embed.add_field(name="👎", value=f"{dislikes}")
            diff = likes - dislikes
            if diff > 0:
                embed.colour = 0x34CB0B
            elif diff < 0:
                embed.colour = 0xCB410B
        if not subject.shortcut.lower().startswith("tv"):
            sem = 1 if subject.semester == "L" else 2
            subject_id = subject.card.split("/")[-2]
            vutis_link = "https://www.vut.cz/studis/student.phtml?script_name=anketa_statistiky"
            embed.add_field(
                name="Další hodnocení",
                value=f"[VUT IS]({vutis_link}&apid={subject_id}&typ_semestru_id={sem})",
                inline=False,
            )
        utils.add_author_footer(embed, msg_author, additional_text=[f"Review: {page} | ID: {id}"])
        return embed

    def update_embed(self, embed: disnake.Embed, review: Review, text_page: int = 1):
        """Update embed fields"""
        embed.colour = 0x6D6A69
        text = review.text_review
        idx = 3
        add_new_field = False
        fields_cnt = len(embed.fields)
        if text is not None:
            text_len = len(text)
            if text_len > 1024:
                pages = text_len // 1024 + (text_len % 1024 > 0)
                text_index = 1024 * (text_page - 1)
                if len(review.text_review) < 1024 * text_page:
                    text = review.text_review[text_index:]
                else:
                    text = review.text_review[text_index: 1024 * text_page]
                embed.set_field_at(idx, name="Text page", value=f"{text_page}/{pages}", inline=False)
                idx += 1
            embed.set_field_at(idx, name="Text", value=text, inline=False)
            idx += 1
        likes = self.repo.get_votes_count(review.id, True)
        embed.set_field_at(idx, name="👍", value=f"{likes}")
        dislikes = self.repo.get_votes_count(review.id, False)
        idx += 1
        if add_new_field or fields_cnt <= idx:
            embed.add_field(name="👎", value=f"{dislikes}")
            add_new_field = True
        else:
            embed.set_field_at(idx, name="👎", value=f"{dislikes}")
        idx += 1
        if not review.shortcut.lower().startswith("tv"):
            # don't remove IS link field on fit courses
            idx += 1
        for _ in range(fields_cnt - idx):
            embed.remove_field(idx)
        diff = likes - dislikes
        if diff > 0:
            embed.colour = 0x34CB0B
        elif diff < 0:
            embed.colour = 0xCB410B
        return embed

    def add_review(self, author_id: int, subject: str, tier: int, anonym: bool, text: str):
        """Add new review, if review with same author and subject exists -> update"""
        if not self.repo.get_subject(subject).first():
            return False
        update = self.repo.get_review_by_author_subject(author_id, subject)
        if update:
            self.repo.update_review(update.id, tier, anonym, text)
        else:
            self.repo.add_review(author_id, subject, tier, anonym, text)
        return True

    def list_reviews(self, author: disnake.User, subject: str):
        subject_obj = self.repo.get_subject(subject).first()
        if not subject_obj:
            subject_obj = self.repo.get_subject(f"tv-{subject}").first()
            if not subject_obj:
                return None
        reviews = self.repo.get_subject_reviews(subject_obj.shortcut)
        reviews_cnt = reviews.count()
        subject_details = self.repo.get_subject_details(subject_obj.shortcut)
        if reviews_cnt == 0:
            description = f"{subject_details.name}\n*No reviews*"
            return [self.make_embed(author, None, subject_details, description, "1/1")]
        else:
            embeds = []
            for idx in range(reviews_cnt):
                review = reviews[idx].Review
                description = f"{subject_details.name}\n**Average tier:** {round(reviews[idx].avg_tier)}"
                page = f"{idx+1}/{reviews_cnt}"

                embeds.append(self.make_embed(author, review, subject_details, description, page))
            return embeds

    def remove(self, author: str, subject: str):
        """Remove review from DB"""
        result = self.repo.get_review_by_author_subject(author, subject)
        if result:
            self.repo.remove(result.id)
            return True
        else:
            return False

    def add_vote(self, review_id: int, vote: bool, author: str):
        """Add/update vote for review"""
        relevance = self.repo.get_vote_by_author(review_id, author)
        if not relevance or relevance.vote != vote:
            self.repo.add_vote(review_id, vote, author)

    def update_subject_types(self, link: str, MIT: bool):
        """Send request to `link`, parse page and find all subjects.
        Add new subjects to DB, if subject already exists update its years.
        For MITAI links please set `MIT` to True.
        If update succeeded return True, otherwise False
        """
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

        programmme_db = self.repo.get_programme(specialization)
        if not programmme_db or programmme_db.link != link:
            self.repo.set_programme(specialization, full_specialization, link)

        sem = 1
        year = 1
        for table in tables:
            rows = table.select("tbody tr")
            for row in rows:
                shortcut = row.find_all("th")[0].get_text()
                # update subject DB
                if not self.repo.get_subject(shortcut.lower()).first():
                    self.repo.add_subject(shortcut.lower())
                columns = row.find_all("td")
                name = columns[0].get_text()
                type = columns[2].get_text()
                degree = "BIT"
                for_year = "VBIT"
                if type == "P":
                    if MIT and year > 2:
                        # any year
                        for_year = f"L{specialization}"
                    else:
                        for_year = f"{year}{specialization}"
                else:
                    if MIT:
                        for_year = "VMIT"
                if MIT:
                    degree = "MIT"
                detail = self.repo.get_subject_details(shortcut)
                semester = "Z"
                if sem == 2:
                    semester = "L"
                if not detail:
                    # subject not in DB
                    self.repo.set_subject_details(
                        shortcut,
                        name,
                        columns[1].get_text(),  # credits
                        semester,
                        columns[3].get_text(),  # end
                        columns[0].find("a").attrs["href"],  # link
                        type,
                        for_year,
                        degree,
                    )
                else:
                    changed = False
                    if name != detail.name:
                        # Update name mainly for courses that are not opened
                        detail.name = name
                        changed = True
                    if for_year not in detail.year.split(", "):
                        # subject already in DB with different year (applicable mainly for MIT)
                        if type not in detail.type.split(", "):
                            detail.type += f", {type}"
                        if detail.year:
                            detail.year += f", {for_year}"
                        changed = True
                    if semester not in detail.semester.split(", "):
                        # subject already in DB with different semester (e.g. RET)
                        detail.semester += f", {semester}"
                        changed = True
                    if degree not in detail.degree.split(", "):
                        # subject already in DB with different degree (e.g. RET)
                        detail.degree += f", {degree}"
                        changed = True
                    if changed:
                        self.repo.update_subject(detail)
            sem += 1
            if sem == 3:
                year += 1
                sem = 1
        return True

    def update_sport_subjects(self):
        sports_list = sports.VutSports().get_sports()
        for item in sports_list:
            if not self.repo.get_subject(item.shortcut.lower()).first():
                self.repo.add_subject(item.shortcut.lower())
                self.repo.set_subject_details(
                    item.shortcut,
                    item.name,
                    1,
                    item.semester.value,
                    "Za",
                    item.subject_id,
                    "V",
                    "VBIT, VMIT",
                    "BIT, MIT",
                )
