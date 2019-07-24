import mysql.connector
from mysql.connector.cursor import MySQLCursor

from config import config, messages


class BaseRepository:

    def __init__(self):
        self.config = config.Config
        self.messages = messages.Messages
        self.db = mysql.connector.connect(**self.config.connection)

    def query_single(self, sql: str, *args, **kwargs) -> MySQLCursor:
        if not self.db.is_connected():
            self.db = mysql.connector.connect(**self.config.connection)

        cursor = self.db.cursor()
        cursor.execute(sql, *args, **kwargs)
        return cursor

    def get_row(self, table: str, where: str, value: str):
        cursor = self.query_single(f"SELECT * FROM {table} WHERE {where} = %s",
                                   (str(value),))
        row = cursor.fetchone()
        return row

    def get_count(self, table: str):
        cursor = self.query_single(f"SELECT COUNT(*) FROM {table}")
        row = cursor.fetchone()
        return row[0]

    def cleanup(self):
        if self.db.is_connected():
            self.db.close()
