import os
import uuid
from random import choice
from flask import Blueprint, Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
from app.models import db
from app.models.user import User, Plan
import jwt
from datetime import datetime, timedelta

load_dotenv()  # This loads the environment variables from .env file

api_login = Blueprint("login", __name__, url_prefix="")




@api_login.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()

    first_name = data.get('firstName')
    last_name = data.get('lastName')
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Missing required fields"}), 400

    if User.query.filter_by(username=email).first():
        print("Email already exists")
        return jsonify({"error": "Email already registered"}), 400

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    new_user = User(username=email, email=email, first_name=first_name, last_name=last_name, password=hashed_password)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User created successfully"}), 201



@api_login.route('/login', methods=['POST'])
def login():
    print("Login route accessed")
    data = request.get_json()
    print(f"Received data: {data}")

    username = data['username']
    password = data['password']
    print(f"Attempting login for user: {username}")

    user = User.query.filter_by(username=username).first()
    print(f"User found: {user is not None}")

    if not user or not check_password_hash(user.password, password):
        print("Invalid username or password")
        return jsonify({"error": "Invalid username or password"}), 400

    print("Login successful")
    # Check if user has any subscription
    has_subscription = user.subscription is not None
    print(f"User has subscription: {has_subscription}")

    return jsonify({
        "message": f"Welcome {user.username}!",
        "username": user.username,
        "success": True,
        "has_subscription": has_subscription,
        "is_subaccount": user.is_subaccount
    }), 200




@api_login.route('/user-profile/<username>', methods=['GET'])
def get_user_profile(username):
    try:
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify({
            "firstName": user.first_name,
            "lastName": user.last_name,
            "email": user.email
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_login.route('/update-profile', methods=['POST'])
def update_profile():
    try:
        data = request.get_json()
        username = data.get('username')
        
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        user.first_name = data.get('firstName', user.first_name)
        user.last_name = data.get('lastName', user.last_name)
        
        db.session.commit()
        return jsonify({"message": "Profile updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@api_login.route('/change-password', methods=['POST'])
def change_password():
    try:
        data = request.get_json()
        username = data.get('username')
        current_password = data.get('currentPassword')
        new_password = data.get('newPassword')

        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        if not check_password_hash(user.password, current_password):
            return jsonify({"error": "Current password is incorrect"}), 400

        user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
        db.session.commit()
        
        return jsonify({"message": "Password updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@api_login.route('/check-permissions', methods=['GET'])
def check_permissions():
    username = request.args.get('username')
    if not username:
        return jsonify({"error": "Username is required"}), 400

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Check if user has an active subscription
    has_game_master = False
    if user.subscription and user.subscription.status == 'active':
        plan = Plan.query.get(user.subscription.plan_id)
        has_game_master = plan and "Game Master" in plan.name

    return jsonify({
        "has_game_master": has_game_master
    }), 200