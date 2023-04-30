# Database-related things

## Connecting to the DB through Docker (externally)

```
docker exec -it $(docker ps -aqf "name=rubbergod-db-1") psql -U postgres
```

PostgreSQL prompt will open and you can now run any SQL (or Postgre-specific) commands you want. To quit, press Ctrl+D.
