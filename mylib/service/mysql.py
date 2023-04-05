from configparser import ConfigParser

import pymysql


class MySQLService:
    def __init__(self):
        self.config = ConfigParser()
        self.config.read('.env')
        self.host = self.config.get('mysql', 'host')
        self.port = self.config.getint('mysql', 'port')
        self.username = self.config.get('mysql', 'username')
        self.password = self.config.get('mysql', 'password')
        self.database = self.config.get('mysql', 'database')

    def get_connection(self):
        conn = pymysql.connect(host=self.host, user=self.username, password=self.password, database=self.database, port=self.port)
        return conn
