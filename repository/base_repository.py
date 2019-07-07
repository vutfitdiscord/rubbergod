import mysql.connector
from config import config


class BaseRepository:

    def __init__(self):
        self.config = config.Config()

    def get_row(self, table, where, value):
        db = mysql.connector.connect(**self.config.connection)
        cursor = db.cursor()
        cursor.execute("SELECT * FROM {} WHERE {} = %s"
                       .format(table, where), (value,))
        row = cursor.fetchone()
        db.close()
        return row
