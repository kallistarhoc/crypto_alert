import sqlite3

connection = sqlite3.connect('database.db')


with open('schema.sql') as f:
    connection.executescript(f.read())

cur = connection.cursor()

cur.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            ('Kast', 'kallista@mail.com', 'password')
            )

cur.execute("INSERT INTO alerts (user_id, base_id, quote_id, alert_condition) VALUES (?, ?, ?, ?)",
            (1, "BTC", "USD", "> 7000")
            )

connection.commit()
connection.close()