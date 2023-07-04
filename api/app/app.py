import datetime
from functools import wraps
import os
import sqlite3
import time
from flask import Flask, request, jsonify, session
import requests
from flask_mail import Mail, Message
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
import jwt

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

app.config["SECRET_KEY"] = os.urandom(24)

app.config["MAIL_SERVER"] = "sandbox.smtp.mailtrap.io"
app.config["MAIL_PORT"] = 2525
app.config["MAIL_USERNAME"] = "0175f0790c03d2"
app.config["MAIL_PASSWORD"] = "8c9d119700267c"
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USE_SSL"] = False

mail = Mail(app)

API_KEY = "CA2C99A8-9F7E-47A4-9B44-1F6FA1C81AED"
HEADERS = {
    "X-CoinAPI-Key": API_KEY,
    "Accept": "application/json",
    "Accept-Encoding": "deflate, gzip",
}


def db_con():
    conn = sqlite3.connect("./database.db")
    conn.row_factory = sqlite3.Row
    return conn


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        db = db_con()
        token = None
        # jwt is passed in the request header
        if "x-access-token" in request.headers:
            token = request.headers["x-access-token"]
        # return 401 if token is not passed
        if not token:
            return jsonify({"message": "Token is missing"}), 401

        try:
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            query = "SELECT * FROM users WHERE id = ?"
            current_user = db.execute(query, (data["id"],)).fetchone()
        except:
            return jsonify({"message": "Invalid token", "token": token}), 401
        # returns the current logged in users context to the routes
        return f(current_user, *args, **kwargs)

    return decorated


@app.route("/register", methods=["POST"])
def register():
    db = db_con()
    username = request.json.get("username")
    email = request.json.get("email")
    password = request.json.get("password")

    query = "SELECT id FROM users WHERE username = ?"
    result = db.execute(query, (username,)).fetchone()
    if result:
        return jsonify({"message": "Username already exists"}), 409

    query = "SELECT id FROM users WHERE email = ?"
    result = db.execute(query, (email,)).fetchone()
    if result:
        return jsonify({"message": "Email already exists"}), 409

    query = "INSERT INTO users (username, email, password) VALUES (?, ?, ?)"
    db.execute(query, (username, email, password))
    db.commit()

    return jsonify({"message": "User registered successfully"}), 201


@app.route("/login", methods=["POST"])
def login():
    db = db_con()
    username = request.json.get("username")
    password = request.json.get("password")

    if not username or not password:
        return jsonify({"message": "Missing required fields"}), 400

    query = "SELECT * FROM users WHERE username = ?"
    user = db.execute(query, (username,)).fetchone()
    if user and user["password"] == password:
        token = jwt.encode(
            {
                "id": user["id"],
                "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30),
            },
            app.config["SECRET_KEY"],
            algorithm="HS256",
        )
        print(token)
        data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        print(data["id"])
        return jsonify({"message": "Login successful", "token": token}), 200
    else:
        return jsonify({"message": "Invalid username or password"}), 401


@app.route("/logout", methods=["POST"])
@token_required
def logout(user):
    # TODO LOGOUT
    return jsonify({"message": "Logout successful"}), 200


@app.route("/users", methods=["PUT", "DELETE"])
@token_required
def update_user(user):
    db = db_con()
    user_id = user["id"]
    if request.method == "PUT":
        username = request.json.get("username")
        password = request.json.get("password")

        query = "UPDATE users SET username = ?, password = ? WHERE id = ?"
        db.execute(query, (username, password, user_id))
        db.commit()

        return jsonify({"message": "User updated successfully"})

    elif request.method == "DELETE":
        query = "DELETE FROM users WHERE id = ?"
        db.execute(query, (user_id,))
        db.commit()

        return jsonify({"message": "User deleted successfully"})

    return jsonify({"message": "Method not allowed"}), 405


@app.route("/alerts", methods=["POST"])
@token_required
def create_alert(user):
    try:
        user_id = user["id"]
        base_id = request.json.get("base_id")
        quote_id = request.json.get("quote_id")
        alert_condition = request.json.get("alert_condition")

        if not user_id or not base_id or not quote_id or not alert_condition:
            return jsonify({"error": "Missing required fields"}), 400

        db = db_con()
        query = "INSERT INTO alerts (user_id, base_id, quote_id, alert_condition) VALUES (?, ?, ?, ?)"
        db.execute(query, (user_id, base_id, quote_id, alert_condition))
        db.commit()

        return jsonify({"message": "Alert created successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/alerts", methods=["GET"])
@token_required
def get_user_alerts(user):
    try:
        # Perform database operation
        user_id = user["id"]
        db = db_con()
        query = "SELECT * FROM alerts WHERE user_id = ?"
        result = db.execute(query, (user_id,)).fetchall()

        # Build response data
        alerts = []
        for row in result:
            alert = {
                "id": row["id"],
                "user_id": row["user_id"],
                "base_id": row["base_id"],
                "quote_id": row["quote_id"],
                "alert_condition": row["alert_condition"],
            }
            alerts.append(alert)

        return jsonify({"alerts": alerts})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/alerts/<int:alert_id>", methods=["DELETE"])
@token_required
def delete_alert(user, alert_id):
    try:
        # Perform database operation
        db = db_con()
        query = "DELETE FROM alerts WHERE id = ?"
        db.execute(query, (alert_id,))
        db.commit()

        return jsonify({"message": "Alert deleted successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/alerts/<int:alert_id>", methods=["GET"])
@token_required
def get_alert(user, alert_id):
    try:
        # Perform database operation
        db = db_con()
        query = "SELECT * FROM alerts WHERE id = ?"
        result = db.execute(query, (alert_id,)).fetchone()

        # Build response data
        alert = {
            "id": result["id"],
            "user_id": result["user_id"],
            "base_id": result["base_id"],
            "quote_id": result["quote_id"],
            "alert_condition": result["alert_condition"],
        }

        # get info from CoinAPI
        res = requests.get(
            f'https://rest.coinapi.io/v1/exchangerate/{alert["base_id"]}/{alert["quote_id"]}',
            headers=HEADERS,
        )
        if res.status_code != 200:
            return jsonify({"error": "Invalid crypto or currency"}), 400
        return jsonify({"alert": alert, "rate": res.json()["rate"]})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/utils/assets", methods=["GET"])
def get_assets():
    try:
        # get all assets from CoinAPI
        res = requests.get(f"https://rest.coinapi.io/v1/assets", headers=HEADERS)
        if res.status_code != 200:
            return jsonify({"code": res.status_code}), 400
        # Build response data
        assets = []
        for asset in res.json():
            assets.append({"id": asset["asset_id"], "name": asset["name"]})
        return jsonify({"assets": assets})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Background task to check alerts every X seconds and send email if condition is met
def for_each_alerts():
    with app.app_context():
        db = db_con()
        query = "SELECT * FROM alerts"
        result = db.execute(query).fetchall()
        if result is None:
            return jsonify({"message": "No alerts found"}), 404
        for row in result:
            alert = {
                "id": row["id"],
                "user_id": row["user_id"],
                "base_id": row["base_id"],
                "quote_id": row["quote_id"],
                "alert_condition": row["alert_condition"],
            }
            check_alerts_condition(alert)


def check_alerts_condition(alert):
    try:
        condition = {
            "symbol": alert["alert_condition"][0],
            "value": alert["alert_condition"][2:],
        }

        # get rate from CoinAPI
        res = requests.get(
            f'https://rest.coinapi.io/v1/exchangerate/{alert["base_id"]}/{alert["quote_id"]}',
            headers=HEADERS,
        )
        if res.status_code != 200:
            return jsonify({"error": "Invalid crypto or currency"}), 400

        #  Build condition string and evaluate
        cond = (
            str(res.json()["rate"])
            + " "
            + condition["symbol"]
            + " "
            + condition["value"]
        )
        if eval(cond):
            return send_email(
                alert["user_id"],
                alert["base_id"],
                alert["quote_id"],
                alert["alert_condition"],
            )
        else:
            print("Alert condition not met")
            return jsonify({"message": "Alert condition not met"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def send_email(user_id, base_id, quote_id, alert_condition):
    db = db_con()
    query = "SELECT * FROM users WHERE id = ?"
    result = db.execute(query, (user_id,)).fetchone()
    if result is None:
        return jsonify({"error": "User not found"}), 404
    print(result["id"], result["username"], result["email"])
    user = {
        "id": result["id"],
        "username": result["username"],
        "email": result["email"],
    }
    print(f"Sending email to user: {user['email']}")
    msg = Message(
        "Crypto Alert", sender="crypto_alert@gmail.com", recipients=[user["email"]]
    )
    msg.body = f"Alert condition met: 1 {base_id} {alert_condition} {quote_id}"
    print(msg)
    try:
        mail.send(msg)
        print(f"Email sent to user: {user['email']}")
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"message": "Email sent successfully"}), 200


# if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
#     sched = BackgroundScheduler()
#     sched.add_job(for_each_alerts, trigger="interval", seconds=180)
#     sched.start()

#     atexit.register(lambda: sched.shutdown())
