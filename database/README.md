# Database-related things

## Connecting to the DB through Docker (externally)

```bash
docker compose exec -it db psql -U postgres
```

PostgreSQL prompt will open and you can now run any SQL (or Postgre-specific) commands you want. To quit, press Ctrl+D.

## Enable debug prints

Add `echo=True` to `database/__init__.py`:

```python
12      self.db = create_engine(self.config.db_string, echo=True)
                                                       ^
```

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

> The `noqa` formula is for linter to ignore seemingly unused import.

## Database backup/restore

> [!Note]
> For these operations you need the database container running.
> ```bash
> docker compose up -d db
> ```

To backup the database, run the following command:

```bash
docker compose exec db pg_dump -U postgres -d postgres > backup.sql
```

To restore the database, run the following commands:

```bash
# remove all tables from the database
docker compose exec db psql -U postgres -c "DROP SCHEMA public CASCADE;CREATE SCHEMA public;GRANT ALL ON SCHEMA public TO postgres;GRANT ALL ON SCHEMA public TO public;"

# restore the database from the backup
docker compose exec -T db psql -U postgres < backup.sql
```

You can drop specific table using this command:

```bash
docker compose exec db psql -U postgres -c "DROP TABLE [table_name] CASCADE;"
```

To get only specific table and it's data use this command:

```bash
docker compose exec db pg_dump -U postgres -d postgres -t [table_name] > [table_name].sql
```
