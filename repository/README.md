## Database-related things

### Connecting to the DB through Docker (externally)

```
docker exec -it $(docker ps -aqf "name=rubbergod-db-1") psql -U postgres
```

PostgreSQL prompt will open and you can now run any SQL (or Postgre-specific) commands you want. To quit, press Ctrl+D.

### Create new table at the start of the Bot

Create a new module with DB structure class ( example from `MemeRepost`):
```
from sqlalchemy import Column, String

from repository.database import database


class MemeRepost(database.base):
    __tablename__ = "bot_meme_reposts"

    original_message_id = Column(String, primary_key=True, nullable=False, unique=True)
    author_id = Column(String, nullable=False)
    reposted_message_id = Column(String, nullable=False)
    secondary_repost_message_id = Column(String, nullable=True)
```

Add the following into `repository/db_migrations.py`:

```
from repository.database.meme_repost import MemeRepost  # noqa: F401
```

> That way, the module gets imported on startup and creates the table automatically.

> The `noqa` formula is for `flake8` to ignore seemingly unused import.
