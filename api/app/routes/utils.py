import datetime
from functools import wraps
import hashlib
from flask import request, jsonify
import jwt
from app import app
import requests
from app.database import db_con
from ..config import Config


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        db = db_con()
        token = None
        # jwt is passed in the request header
        print(request.headers)
        if "x-access-token" in request.headers:
            token = request.headers["x-access-token"]
        # return 401 if token is not passed
        print(token)
        if not token:
            return jsonify({"message": "Token is missing"}), 401
        # check if token is blacklisted
        query = "SELECT * FROM blacklisted_tokens WHERE token = ?"
        blacklisted_token = db.execute(query, (token,)).fetchone()
        if blacklisted_token:
            return jsonify({"message": "Token is invalid"}), 401
        try:
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            query = "SELECT * FROM users WHERE id = ?"
            current_user = db.execute(query, (data["id"],)).fetchone()
        except:
            return jsonify({"message": "Invalid token", "token": token}), 401
        # returns the current logged in users context to the routes
        return f(current_user, *args, **kwargs)

    return decorated

def generate_token(user_id):
    try:
        token = jwt.encode(
            {
                "id": user_id,
                "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30),
            },
            Config.SECRET_KEY,
            algorithm="HS256",
        )
        return token
    except Exception as e:
        print(str(e))
        return jsonify({"error": str(e)}), 500

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hash):
    return hash_password(password) == hash