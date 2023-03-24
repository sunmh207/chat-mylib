from configparser import ConfigParser
import pymysql

class MySQLService:
    config = ConfigParser()
    config.read('.env')
    HOST = config.get('mysql','host')
    PORT = config.getint('mysql','port')
    USERNAME = config.get('mysql','username')
    PASSWORD = config.get('mysql','password')
    DATABASE = config.get('mysql','database')

    def get_connection(self):
        conn = pymysql.connect(host=self.HOST, user=self.USERNAME, password=self.PASSWORD, database=self.DATABASE, port=self.PORT)
        return conn


