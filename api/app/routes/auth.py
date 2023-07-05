from flask import Blueprint, jsonify, request
from app.database import db_con
from .utils import generate_token, hash_password, verify_password, token_required

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    try:
        username = request.json.get("username")
        email = request.json.get("email")
        password = request.json.get("password")

        if not email or not password or not username:
            return jsonify({"error": "Missing required fields"}), 400
        query = "SELECT id FROM users WHERE email = ?"
        db = db_con()
        result = db.execute(query, (email,)).fetchone()
        if result:
            return jsonify({"message": "Email already exists"}), 409
        hashed_password = hash_password(password)
        query = "INSERT INTO users (email, username, password) VALUES (?, ?, ?)"
        db.execute(query, (email, username, hashed_password))
        db.commit()
        return jsonify({"message": "User registered successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        email = request.json.get("email")
        password = request.json.get("password")

        if not email or not password:
            return jsonify({"error": "Missing required fields"}), 400

        db = db_con()
        query = "SELECT * FROM users WHERE email = ?"
        result = db.execute(query, (email,)).fetchone()
        print(result)
        if result is None:
            return jsonify({"error": "Invalid credentials"}), 401
        user = {
            "id": result["id"],
            "email": result["email"],
            "username": result["username"],
        }

        stored_password = result["password"]
        if not verify_password(password, stored_password):
            return jsonify({"error": "Invalid credentials"}), 401

        user_id = result["id"]
        token = generate_token(user_id)
        return jsonify({"token": token, "user": user})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@auth_bp.route("/logout", methods=["POST"])
@token_required
def logout(user):
    try:
        user_id = user["id"]
        token = request.headers.get("x-access-token")
        db = db_con()
        print(token)
        print(user_id)
        query = "INSERT INTO blacklisted_tokens (token, user_id) VALUES (?, ?)"
        db.execute(query, (token, user_id))
        db.commit()
        return jsonify({"message": "User logged out successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    