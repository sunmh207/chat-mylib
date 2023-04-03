from configparser import ConfigParser
import pymysql

class MySQLService:
    def __init__(self):
        self.config = ConfigParser()
        self.config.read('.env')
        self.HOST = self.config.get('mysql', 'host')
        self.PORT = self.config.getint('mysql', 'port')
        self.USERNAME = self.config.get('mysql', 'username')
        self.PASSWORD = self.config.get('mysql', 'password')
        self.DATABASE = self.config.get('mysql', 'database')

    def get_connection(self):
        conn = pymysql.connect(host=self.HOST, user=self.USERNAME, password=self.PASSWORD, database=self.DATABASE, port=self.PORT)
        return conn


