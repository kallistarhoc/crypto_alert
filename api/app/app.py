from flask import Flask, render_template
from flask_cors import CORS
from .routes import alerts, auth, users
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import os
import requests
from .database import db_con
from flask import jsonify
from .config import Config
from flask_mail import Mail, Message
from flask import request


app = Flask(__name__)


CORS(app, resources={r"/*": {"origins": "*"}})

app.register_blueprint(alerts.alerts_bp)
app.register_blueprint(auth.auth_bp)
app.register_blueprint(users.users_bp)

app.config['MAIL_SERVER']= Config.MAIL_SERVER
app.config['MAIL_PORT'] = Config.MAIL_PORT
app.config['MAIL_USERNAME'] = Config.MAIL_USERNAME
app.config['MAIL_PASSWORD'] = Config.MAIL_PASSWORD
app.config['MAIL_USE_TLS'] = Config.MAIL_USE_TLS
app.config['MAIL_USE_SSL'] = Config.MAIL_USE_SSL

mail = Mail(app)

@app.route("/utils/assets", methods=["GET"])
def get_assets():
    try:
        # get all assets from CoinAPI
        res = requests.get(
            f"https://rest.coinapi.io/v1/assets", headers=Config.HEADERS
        )
        if res.status_code != 200:
            print(res.status_code)
            print(res.json())
            return jsonify({"code": res.status_code}), 400
        # Build response data
        assets = []
        for asset in res.json():
            assets.append({"id": asset["asset_id"], "name": asset["name"]})
        return jsonify({"assets": assets})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
            headers=Config.HEADERS,
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
        print(e)
        return jsonify({"error": str(e)}), 500
    return jsonify({"message": "Email sent successfully"}), 200

if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    scheduler = BackgroundScheduler()
    scheduler.add_job(for_each_alerts, trigger="interval", seconds=300)
    scheduler.start()

    # Shut down the scheduler when the Flask app is terminated
    atexit.register(lambda: scheduler.shutdown())


if __name__ == "__main__":
    app.run(debug=True)
