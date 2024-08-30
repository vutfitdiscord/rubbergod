import logging

from database import database, session
from database.better_meme import BetterMemeDB  # noqa: F401
from database.contestvote import ContestVoteDB  # noqa: F401
from database.cooldown import CooldownDB  # noqa: F401
from database.error import ErrorLogDB  # noqa: F401
from database.exams import ExamsTermsMessageDB  # noqa: F401
from database.hugs import HugsTableDB  # noqa: F401
from database.image import ImageDB  # noqa: F401
from database.karma import KarmaDB, KarmaEmojiDB  # noqa: F401
from database.meme_repost import MemeRepostDB  # noqa: F401
from database.moderation import ModerationDB  # noqa: F401
from database.pin_map import PinMapDB  # noqa: F401
from database.report import AnswerDB, ReportDB, UserDB  # noqa: F401
from database.review import ReviewDB, ReviewRelevanceDB, SubjectDB, SubjectDetailsDB  # noqa: F401
from database.streamlinks import StreamLinkDB  # noqa: F401
from database.subscription import AlreadyNotifiedDB, SubscriptionDB  # noqa: F401
from database.timeout import TimeoutDB, TimeoutUserDB  # noqa: F401
from database.verification import PermitDB, ValidPersonDB  # noqa: F401
from database.vote import VoteDB  # noqa: F401

rubbergod_logger = logging.getLogger("rubbergod")


def init_db(commit: bool = True):
    # database.base.metadata.drop_all(database.db)
    rubbergod_logger.info("Creating missing tables")
    database.base.metadata.create_all(database.db)
    rubbergod_logger.info("Tables created")

    if commit:
        session.commit()
