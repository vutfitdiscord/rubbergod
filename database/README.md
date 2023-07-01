# Database-related things

## Connecting to the DB through Docker (externally)

```bash
docker exec -it rubbergod-db-1 psql -U postgres
```

PostgreSQL prompt will open and you can now run any SQL (or Postgre-specific) commands you want. To quit, press Ctrl+D.

## Create a new table at the start of the Bot

Create a new module with DB structure class (example from `MemeRepost`):

```python
from __future__ import annotations  # for type hint of self class

from typing import Optional

from sqlalchemy import Column, String

from database import database, session


class MemeRepostDB(database.base):
    __tablename__ = "bot_meme_reposts"

    original_message_id = Column(String, primary_key=True, nullable=False, unique=True)
    author_id = Column(String, nullable=False)
    reposted_message_id = Column(String, nullable=False)
    secondary_repost_message_id = Column(String, nullable=True)

    # example of classmethod for creating a row in database
    # calling: MemeRepostDB.find_by_id()
    @classmethod
    def find_by_id(cls, id: str) -> Optional[MemeRepostDB]:
        return session.query(cls).filter(original_message_id == id).one_or_none()


    # example of method for deleting a row
    # calling:
    #     item = MemeRepostDB.find(id)
    #     item.delete()
    def delete(self):
        session.delete(self)
        session.commit()
```

Add the following into `database/db_migrations.py`:

```python
from database.meme_repost import MemeRepostDB  # noqa: F401
```

That way, the module gets imported on startup and creates the table automatically.

> The `noqa` formula is for `flake8` to ignore seemingly unused import.

## Enable debug prints

Add `echo=True` to `database/__init__.py`:
```python
12      self.db = create_engine(self.config.db_string, echo=True)
                                                       ^
```
