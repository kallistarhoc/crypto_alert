import sqlite3 as sql

def create_user(username,password):
    con = sql.connect("database.db")
    cur = con.cursor()
    cur.execute("INSERT INTO users (username,password) VALUES (?,?)", (username,password))
    con.commit()
    con.close()

def get_user(username,password):
	con = sql.connect("database.db")
	cur = con.cursor()
	cur.execute("SELECT id, username FROM users WHERE username = ? AND password = ?", (username,password))
	user = cur.fetchone()
	con.close()
	return user