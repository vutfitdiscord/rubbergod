import mysql.connector
from mysql.connector.cursor import MySQLCursor

from config import config, messages


class BaseRepository:

    def __init__(self):
        self.config = config.Config
        self.messages = messages.Messages
        self.db = mysql.connector.connect(**self.config.connection)

    def cursor(self):
        if not self.db.is_connected():
            self.db = mysql.connector.connect(**self.config.connection)

        return self.db.cursor()

    def query(self, sql: str, *args, **kwargs) -> MySQLCursor:
        cursor = self.cursor()
        cursor.execute(sql, *args, **kwargs)
        return cursor

    def get_all(self, table: str, where: str = None, value: str = None):
        if where:
            cursor = self.query(f"SELECT * FROM {table} WHERE {where} = %s",
                                (str(value),))
        else:
            cursor = self.query(f"SELECT * FROM {table}")

        rows = cursor.fetchall()
        return rows

    def get_row(self, table: str, where: str, value: str):
        cursor = self.query(f"SELECT * FROM {table} WHERE {where} = %s",
                            (str(value),))
        row = cursor.fetchone()
        return row

    def get_count(self, table: str, where: str = None, value: str = None):
        if where:
            cursor = self.query(
                f"SELECT COUNT(*) FROM {table} "
                f"WHERE {where} = %s", (str(value),))
        else:
            cursor = self.query(f"SELECT COUNT(*) FROM {table}")
        row = cursor.fetchone()
        return row[0]

    def cleanup(self):
        if self.db.is_connected():
            self.db.close()
