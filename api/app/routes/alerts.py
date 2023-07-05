from flask import Blueprint, jsonify, request
from .utils import token_required
from app.database import db_con
from ..config import Config
import requests

alerts_bp = Blueprint("alerts", __name__)


@alerts_bp.route("/alerts", methods=["POST"])
@token_required
def create_alert(current_user):
    try:
        user_id = current_user["id"]
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


@alerts_bp.route("/alerts", methods=["GET"])
@token_required
def get_user_alerts(current_user):
    try:
        user_id = current_user["id"]
        db = db_con()
        query = "SELECT * FROM alerts WHERE user_id = ?"
        result = db.execute(query, (user_id,)).fetchall()

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


@alerts_bp.route("/alerts/<int:alert_id>", methods=["DELETE"])
@token_required
def delete_alert(current_user, alert_id):
    try:
        db = db_con()
        query = "DELETE FROM alerts WHERE id = ?"
        db.execute(query, (alert_id,))
        db.commit()

        return jsonify({"message": "Alert deleted successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@alerts_bp.route("/alerts/<int:alert_id>", methods=["GET"])
@token_required
def get_alert(current_user, alert_id):
    try:
        db = db_con()
        query = "SELECT * FROM alerts WHERE id = ?"
        result = db.execute(query, (alert_id,)).fetchone()
        if not result or result["user_id"] != current_user["id"]:
            return jsonify({"error": "Alert not found"}), 404
        
        # get current exchange rate of the base and quote currencies

        alert = {
            "id": result["id"],
            "user_id": result["user_id"],
            "base_id": result["base_id"],
            "quote_id": result["quote_id"],
            "alert_condition": result["alert_condition"],
        }

        res = requests.get(
            f'https://rest.coinapi.io/v1/exchangerate/{alert["base_id"]}/{alert["quote_id"]}',
            headers=Config.HEADERS,
        )
        print(res.json())
        if res.status_code != 200:
            return jsonify({"error": "Invalid crypto or currency"}), 400

        alert["current_rate"] = res.json()["rate"]

        return jsonify({"alert": alert})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
