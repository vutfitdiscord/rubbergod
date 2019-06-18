from repository.base_repository import BaseRepository
import mysql.connector


class User(BaseRepository):

    def save_record(self, message):
        """"Inserts login with discord name into database"""
        db = mysql.connector.connect(**self.config.connection)
        login = str(message.content).split(" ")[1]  # gets login from command
        cursor = db.cursor()
        cursor.execute('SELECT * FROM bot_valid_persons WHERE login="{}"'
                       .format(login))
        row = cursor.fetchone()
        insert = cursor.execute('INSERT INTO bot_permit '
                                '(login, discord_name, discord_id) '
                                'VALUES ("{}", "{}", {})'
                                .format(login, str(message.author),
                                        message.author.id))
        cursor.execute('UPDATE bot_valid_persons SET status="{}" '
                       'WHERE login="{}"'.format(0, login))
        db.commit()
        db.close()
        return insert

    @staticmethod
    def has_role(message, role):
        """"Checks if user has defined role"""
        has_role = False
        for user_role in message.author.roles:
            if str(user_role) == role:
                has_role = True
        return has_role

    def find_login(self, message):
        """"Finds login from database"""
        db = mysql.connector.connect(**self.config.connection)
        login = str(message.content).split(" ")[1]  # gets login from command
        code = str(message.content).split(" ")[2]  # gets key from command
        cursor = db.cursor()
        cursor.execute('SELECT * FROM bot_valid_persons WHERE `login`="{}" '
                       'AND `code`="{}" AND status = 2'.format(login, code))
        login = cursor.fetchone()
        db.close()
        return login
