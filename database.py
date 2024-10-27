import mysql.connector

class DatabaseConnection:
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None

    def connect(self):
        self.connection = mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database
        )

    def close(self):
        if self.connection:
            self.connection.close()

    def execute_query(self, query, params=None):
        cursor = self.connection.cursor()
        cursor.execute(query, params or ())
        return cursor

    def commit(self):
        self.connection.commit()
