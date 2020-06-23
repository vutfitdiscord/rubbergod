import re

from repository.database import database, session
from repository.database.karma import Karma, Karma_emoji
from repository.database.review import (Review, ReviewRelevance, Subject)
from repository.database.verification import Permit, Valid_person
from repository.database.image import Image
from repository.review_repo import ReviewRepository

from config.config import Config


def init_db(commit: bool = True):
    database.base.metadata.create_all(database.db)

    if commit:
        session.commit()


def load_dump(filename: str):
    init_db(False)

    session.query(Karma).delete()
    session.query(Karma_emoji).delete()
    session.query(Permit).delete()
    session.query(Valid_person).delete()
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
                karma_values.append(Karma(member_ID=values[i],
                                          karma=values[i + 1]))
        elif insert.startswith("INSERT INTO `bot_karma_giving`"):
            values = values[1:-2].replace('\'', '')
            values = values.replace('(', '').replace(')', '')
            values = values.split(',')
            for i in range(0, len(values), 4):
                karma_values.append(Karma(member_ID=values[i],
                                          positive=values[i + 1],
                                          negative=values[i + 2]))
        elif insert.startswith("INSERT INTO `bot_karma_emoji`"):
            values = values[1:-2].replace('\'', '')
            values = values.replace('(', '').replace(')', '')
            values = values.split(',')
            for i in range(0, len(values), 2):
                session.add(Karma_emoji(emoji_ID=values[i],
                                        value=values[i + 1]))
        elif insert.startswith("INSERT INTO `bot_permit`"):
            values = values[1:-2]
            values = values.replace('(', '').replace(')', '')
            values = re.split(r',(?=\')', values)
            values = [value.replace('\'', '') for value in values]
            for i in range(0, len(values), 3):
                session.add(Permit(login=values[i],
                                   discord_ID=values[i + 2]))
        elif insert.startswith("INSERT INTO `bot_valid_persons`"):
            values = values[1:-2].replace('\'', '')
            values = values.replace('(', '').replace(')', '')
            values = values.split(',')
            for i in range(0, len(values), 5):
                session.add(Valid_person(login=values[i],
                                         name=values[i + 1],
                                         year=values[i + 2],
                                         code=values[i + 3]
                                         if values[i + 3] != "NULL" else None,
                                         status=values[i + 4]))

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
    subjects = list(set(Config.subjects))

    review_repo = ReviewRepository()
    for subject in subjects:
        print(f'Importing subject {subject}')
        review_repo.add_subject(subject)
    print('Import complete')
