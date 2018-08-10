import mysql.connector
from config import config


class BaseRepository:

	def __init__(self):
		self.config = config.Config()
		self.db = mysql.connector.connect(**self.config.connection)

	def get_row(self, table, where):
		cursor = self.db.cursor()
		cursor.execute("SELECT * FROM {} WHERE {}".format(table, where))
		row = cursor.fetchone()
		return row
