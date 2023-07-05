import sqlite3 as sql
from .config import Config

def db_con():
    conn = sql.connect(Config.DB_NAME)
    conn.row_factory = sql.Row
    return conn
