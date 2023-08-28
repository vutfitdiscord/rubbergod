import re

from config.app_config import config
from database import database, session
from database.better_meme import BetterMemeDB  # noqa: F401
from database.cooldown import CooldownDB  # noqa: F401
from database.error import ErrorLogDB  # noqa: F401
from database.exams import ExamsTermsMessageDB  # noqa: F401
from database.hugs import HugsTableDB
from database.image import ImageDB  # noqa: F401
from database.karma import KarmaDB, KarmaEmojiDB
from database.meme_repost import MemeRepostDB  # noqa: F401
from database.pin_map import PinMapDB  # noqa: F401
from database.report import AnswerDB, ReportDB, UserDB  # noqa: F401
from database.review import ReviewDB  # noqa: F401
from database.review import ReviewRelevanceDB  # noqa: F401
from database.review import SubjectDetailsDB  # noqa: F401
from database.review import SubjectDB
from database.role_group import RoleGroupDB  # noqa: F401
from database.streamlinks import StreamLinkDB  # noqa: F401
from database.subscription import AlreadyNotifiedDB  # noqa: F401
from database.subscription import SubscriptionDB  # noqa: F401
from database.timeout import TimeoutDB  # noqa: F401
from database.verification import PermitDB, ValidPersonDB
from database.vote import VoteDB  # noqa: F401


def init_db(commit: bool = True):
    # database.base.metadata.drop_all(database.db)
    database.base.metadata.create_all(database.db)

    if commit:
        session.commit()


def load_dump(filename: str):
    init_db(False)

    session.query(KarmaDB).delete()
    session.query(KarmaEmojiDB).delete()
    session.query(PermitDB).delete()
    session.query(ValidPersonDB).delete()
    session.query(HugsTableDB).delete()
    session.commit()

    print(f'Loading dump from {filename}')

    data = database.base.metadata.tables.keys()
    for row in data:
        print(row)

    with open(filename, "r", encoding='utf-8') as backup_file:
        data = backup_file.readlines()

    inserts = [line for line in data if line.startswith("INSERT")]
    karma_values = []

    for insert in inserts:
        values = insert.split("VALUES", 1)[1]
        if insert.startswith("INSERT INTO `bot_karma`"):
            values = values[1:-2].replace('\'', '')
            values = values.replace('(', '').replace(')', '')
            values = values.split(',')
            for i in range(0, len(values), 3):
                karma_values.append(KarmaDB(member_ID=values[i], karma=values[i + 1]))
        elif insert.startswith("INSERT INTO `bot_karma_giving`"):
            values = values[1:-2].replace('\'', '')
            values = values.replace('(', '').replace(')', '')
            values = values.split(',')
            for i in range(0, len(values), 4):
                karma_values.append(KarmaDB(member_ID=values[i],
                                            positive=values[i + 1],
                                            negative=values[i + 2]))
        elif insert.startswith("INSERT INTO `bot_karma_emoji`"):
            values = values[1:-2].replace('\'', '')
            values = values.replace('(', '').replace(')', '')
            values = values.split(',')
            for i in range(0, len(values), 2):
                session.add(KarmaEmojiDB(emoji_ID=values[i], value=values[i + 1]))
        elif insert.startswith("INSERT INTO `bot_permit`"):
            values = values[1:-2]
            values = values.replace('(', '').replace(')', '')
            values = re.split(r',(?=\')', values)
            values = [value.replace('\'', '') for value in values]
            for i in range(0, len(values), 3):
                session.add(PermitDB(login=values[i], discord_ID=values[i + 2]))
        elif insert.startswith("INSERT INTO `bot_valid_persons`"):
            values = values[1:-2].replace('\'', '')
            values = values.replace('(', '').replace(')', '')
            values = values.split(',')
            for i in range(0, len(values), 5):
                session.add(ValidPersonDB(
                    login=values[i],
                    name=values[i + 1],
                    year=values[i + 2],
                    code=values[i + 3]
                    if values[i + 3] != "NULL" else None,
                    status=values[i + 4])
                )

    for karma in karma_values:
        session.merge(karma)

    session.commit()


def load_subjects():
    """
    Fills DB with subject shorcut from config file.
    This is needed for reviews feature.
    Run this just when you want to create DB fo reviews.
    """

    # Remove duplicates
    subjects = list(set(config.subjects))

    for subject in subjects:
        print(f'Importing subject {subject}')
        SubjectDB.add(subject)
    print('Import complete')
