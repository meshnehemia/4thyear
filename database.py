import mysql.connector

def connect():
    try:
        conn = mysql.connector.connect(
            host="127.0.0.1",  # e.g., 'localhost' or '127.0.0.1'
            user="root",  # your MySQL username
            password="",  # your MySQL password
            database="supermarket"  # your database name
        )
        return conn
    except mysql.connector.Error as err:
        return None
