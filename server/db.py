from dotenv import load_dotenv
import os
import mysql.connector

load_dotenv()

class Journal:

    def __init__(self) -> None:
        self.host = os.getenv("HOST"),
        self.user = os.getenv("USERNAME"),
        self.password = os.getenv("PASSWORD"),
        self.db = os.getenv("DATABASE"),
        self.ssl_verify_identity = True,
        self.ssl_ca = '/etc/ssl/cert.pem',
        self.conn = None

    def connect(self):
        if self.conn is None:
            self.conn = mysql.connector.connect(
                host = self.host,
                user = self.user,
                password = self.password,
                db = self.db,
                ssl_verify_identity = True,
                ssl_ca = '/etc/ssl/cert.pem',
            )
            print('Database Connected Successfully!')

    def retrieve_entries(self, username):
        self.connect()
        cursor = self.conn.cursor(dictionary=True)
        cursor.execute("SELECT title, journal_entry FROM Journal WHERE username='%s';", (username))
        results = cursor.fetchall()
        cursor.close()
        return results




