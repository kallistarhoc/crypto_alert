DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    auth_token TEXT,
    password TEXT NOT NULL
);

DROP TABLE IF EXISTS alerts;

CREATE TABLE alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    base_id TEXT NOT NULL,
    quote_id TEXT NOT NULL,
    alert_condition TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

DROP TABLE IF EXISTS jwt_tokens;

CREATE TABLE jwt_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);