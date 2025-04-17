import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.user = os.getenv('DB_USER', 'root')
        self.password = os.getenv('DB_PASSWORD', '')
        self.database = os.getenv('DB_NAME', 'green_buddy')

    def get_connection(self):
        try:
            connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=3306,  
                connect_timeout=10  
            )
            if connection.is_connected():
                db_info = connection.get_server_info()
                cursor = connection.cursor()
                cursor.execute("select database();")
                db_name = cursor.fetchone()[0]
                cursor.close()
                return connection
            else:
                print("Connection object created but not connected")
                return None
        except Error as e:
            print("\n=== ERROR: Database Connection Failed ===")
            print(f"Error type: {type(e)}")
            print(f"Error message: {str(e)}")
            print(f"Error code: {getattr(e, 'errno', 'N/A')}")
            print(f"SQL State: {getattr(e, 'sqlstate', 'N/A')}")
            print(f"Error details: {e}")
            return None 