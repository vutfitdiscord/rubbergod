import mysql.connector
from config import config, messages


class BaseRepository:

    def __init__(self):
        self.config = config.Config
        self.messages = messages.Messages

    def get_row(self, table, where, value):
        db = mysql.connector.connect(**self.config.connection)
        cursor = db.cursor()
        cursor.execute("SELECT * FROM {} WHERE {} = %s"
                       .format(table, where), (str(value),))
        row = cursor.fetchone()
        db.close()
        return row
