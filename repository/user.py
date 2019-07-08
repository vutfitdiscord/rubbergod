from repository.base_repository import BaseRepository
import mysql.connector


class User(BaseRepository):

    def save_mail(self, message, code):
        """"Inserts login with discord name into database"""
        db = mysql.connector.connect(**self.config.connection)
        login = str(message.content).split(" ")[1]  # gets login from command
        cursor = db.cursor()
        cursor.execute('UPDATE bot_valid_persons SET status=%s, code=%s'
                       'WHERE login=%s', (2, code, login))
        db.commit()
        db.close()
        return

    def save_record(self, message):
        """"Inserts login with discord name into database"""
        db = mysql.connector.connect(**self.config.connection)
        login = str(message.content).split(" ")[1]  # gets login from command
        cursor = db.cursor()
        cursor.execute('SELECT * FROM bot_valid_persons WHERE login=%s',
                       (login,))
        cursor.fetchone()
        insert = cursor.execute('INSERT INTO bot_permit '
                                '(login, discord_name, discord_id) '
                                'VALUES (%s, %s, %s)',
                                (login, str(message.author),
                                 message.author.id))
        cursor.execute('UPDATE bot_valid_persons SET status=%s '
                       'WHERE login=%s', (0, login))
        db.commit()
        db.close()
        return insert

    @staticmethod
    def has_role(message, role):
        """"Checks if user has defined role"""
        try:
            return True if role in message.author.roles else False
        except AttributeError:
            return False

    def find_login_to_mail(self, message):
        """"Finds login from database"""
        db = mysql.connector.connect(**self.config.connection)
        login = str(message.content).split(" ")[1]  # gets login from command
        cursor = db.cursor()
        cursor.execute('SELECT * FROM bot_valid_persons WHERE `login`=%s '
                       'AND status = 1', (login,))
        login = cursor.fetchone()
        db.close()
        return login

    def find_login(self, message):
        """"Finds login from database"""
        db = mysql.connector.connect(**self.config.connection)
        login = str(message.content).split(" ")[1]  # gets login from command
        code = str(message.content).split(" ")[2]  # gets key from command
        cursor = db.cursor()
        cursor.execute('SELECT * FROM bot_valid_persons WHERE `login`=%s '
                       'AND `code`=%s AND status = 2', (login, code))
        login = cursor.fetchone()
        db.close()
        return login
