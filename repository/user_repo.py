from repository.base_repository import BaseRepository


class UserRepository(BaseRepository):
    # Status 0 = verified
    # Status 1 = unverified
    # Status 2 = in process of verification

    def save_sent_code(self, login: str, code: str):
        """Updates a specified login with a new verification code"""

        cursor = self.cursor()
        cursor.execute('UPDATE bot_valid_persons SET status=%s, code=%s '
                       'WHERE login=%s', (2, code, login))
        self.db.commit()
        cursor.close()

    def save_verified(self, login: str, discord_name: str, discord_id: str):
        """"Inserts login with discord name into database"""
        cursor = self.cursor()

        cursor.execute('INSERT INTO bot_permit '
                       '(login, discord_name, discord_id) '
                       'VALUES (%s, %s, %s)',
                       (login, discord_name, discord_id))

        cursor.execute('UPDATE bot_valid_persons SET status=0 '
                       'WHERE login=%s', (login,))
        self.db.commit()
        cursor.close()

    def has_unverified_login(self, login: str):
        """"Checks if there's a login """
        cursor = self.cursor()
        cursor.execute('SELECT * FROM bot_valid_persons WHERE `login`=%s '
                       'AND status = 1', (login,))
        cursor.fetchall()
        rc = cursor.rowcount
        cursor.close()
        return rc

    def get_user(self, login: str, status: int = 2):
        """"Finds login from database"""

        cursor = self.cursor()
        cursor.execute(
            'SELECT login, year, code FROM bot_valid_persons WHERE `login`=%s '
            'AND status = %s', (login, status))
        login = cursor.fetchone()
        cursor.close()
        return login

    def new_user(self, login: str, year: str, status: int = 1):
        """"Finds login from database"""

        cursor = self.cursor()
        cursor.execute(
            'INSERT INTO bot_valid_persons(login, year, status) VALUES'
            '(%s, %s, %s)', (login, year, status))
        cursor.fetchone()
        cursor.close()
        return
