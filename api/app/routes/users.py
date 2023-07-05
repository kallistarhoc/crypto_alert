from flask import Blueprint, jsonify, request
from app.database import db_con
from .utils import token_required, hash_password


users_bp = Blueprint("users", __name__)


@users_bp.route("/users", methods=["PUT", "DELETE"])
@token_required
def update_user(current_user):
    db = db_con()
    user_id = current_user["id"]

    if request.method == "PUT":
        username = request.json.get("username", current_user["username"])
        email = request.json.get("email", current_user["email"])
        if request.json.get("password"):
            hashed_password = hash_password(request.json.get("password"))
        else:
            hashed_password = current_user["password"]
        query = "UPDATE users SET username = ?, email = ?, password = ? WHERE id = ?"
        db.execute(query, (username, email, hashed_password, user_id))
        db.commit()
        return jsonify({"message": "User updated successfully"}), 200

    elif request.method == "DELETE":
        query = "DELETE FROM users WHERE id = ?"
        db.execute(query, (user_id,))
        db.commit()

        return jsonify({"message": "User deleted successfully"}), 200

    return jsonify({"message": "Method not allowed"}), 405


@users_bp.route("/users", methods=["GET"])
@token_required
def get_user(current_user):
    user = {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user["email"],
    }
    return jsonify({"user": user})

@users_bp.route("/users", methods=["DELETE"])
@token_required
def delete_user(current_user):
    user_id = current_user["id"]
    db = db_con()
    query = "DELETE FROM users WHERE id = ?"
    db.execute(query, (user_id,))
    db.commit()
    query = "DELETE FROM alerts WHERE user_id = ?"
    db.execute(query, (user_id,))
    db.commit()

    return jsonify({"message": "User and user's alerts deleted successfully"}), 200