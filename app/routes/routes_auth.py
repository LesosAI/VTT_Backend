import os
import uuid
from random import choice
from flask import Blueprint, Flask, app, jsonify, redirect, request
from flask_cors import CORS
from flask_mail import Message
from flask_sqlalchemy import SQLAlchemy
import requests
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
from app.models import db
from app.utils import mail
from app.models.user import User, Plan
import jwt
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer

load_dotenv()  # This loads the environment variables from .env file

api_login = Blueprint("login", __name__, url_prefix="")

serializer = URLSafeTimedSerializer(os.getenv('SECRET_KEY'))

def generate_verification_token(email: str, purpose: str):
    if purpose == "email-confirm":
        return serializer.dumps(email, salt=purpose)
    elif purpose == "reset_password":
        return serializer.dumps(email, salt=purpose)

@api_login.route('/send-verification', methods=['POST'])
def send_verification_email():
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({"error": "Email is required"}), 400
    
    token = generate_verification_token(email, purpose="email-confirm")
    try:
        send_verification_email_with_graph(email, token)
        return jsonify({"message": "Verification email sent"}), 200
    except Exception as e:
        print(e)
        return jsonify({"error": "Failed to send email"}), 500


@api_login.route('/verify-email', methods=['GET'])
def verify_email():
    token = request.args.get('token')
    try:
        email = serializer.loads(token, salt="email-confirm", max_age=3600)
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found."}), 400

        user.is_verified = True
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        print(e)
        return jsonify({"error": "Invalid or expired token"}), 400


def get_access_token():
    tenant_id = os.getenv("TENANT_ID")
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")

    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials",
    }

    response = requests.post(url, data=payload)
    print(f"Response text: {response.text}")
    response.raise_for_status()
    return response.json()["access_token"]

def send_verification_email_with_graph(recipient_email, token):
    access_token = get_access_token()
    sender_email = os.getenv("SENDER_EMAIL")
    verify_url = f"{os.getenv('DOMAIN')}/verify-email?token={token}"

    html_content = f"""
    <html>
    <body style="margin: 0; padding: 0; background-color: #0f172a; font-family: 'Segoe UI', sans-serif; color: #e5e7eb;">
        <center style="width: 100%; table-layout: fixed; background-color: #0f172a; padding: 40px 0;">
        <div style="max-width: 600px; margin: auto; background-color: #1e1b2e; padding: 30px; border-radius: 12px;">
            
            <!-- Logo -->
            <table role="presentation" width="100%" style="margin-bottom: 30px;">
            <tr>
                <td align="center">
                <img src="https://www.forgelab.pro/_next/image?url=%2FForgeLabsLogo.png&w=750&q=75&dpl=dpl_6vbAiZYyLAhMyJ4wEbYm3wB84kXi" alt="ForgeLab Logo" style="height: 200px;" />
                </td>
            </tr>
            </table>

            <!-- Welcome Text -->
            <h2 style="color: #a78bfa; text-align: center; font-size: 24px; margin: 0 0 20px;">Welcome to ForgeLab</h2>
            <p style="font-size: 16px; line-height: 1.6; text-align: center;">
            You’re almost there. Confirm your email to begin exploring worlds, shaping characters, and crafting unforgettable stories with ForgeLab.
            </p>

            <!-- Bulletproof Button -->
            <table role="presentation" align="center" cellpadding="0" cellspacing="0" style="margin: 30px auto;">
            <tr>
                <td bgcolor="#111827" style="border-radius: 8px; text-align: center;">
                <a href="{verify_url}" style="display: inline-block; padding: 14px 28px; font-size: 15px; color: #ffffff; background-color: #111827; border: 1px solid #a78bfa; text-decoration: none; font-weight: 600; border-radius: 8px;">
                    Verify My Email
                </a>
                </td>
            </tr>
            </table>

            <!-- Link Alternative -->
            <p style="font-size: 14px; color: #cbd5e1; margin-top: 40px;">
            Or copy and paste this link into your browser:
            </p>
            <p style="word-break: break-all;">
            <a href="{verify_url}" style="color: #a78bfa;">{verify_url}</a>
            </p>

            <!-- Footer -->
            <p style="margin-top: 40px; font-size: 14px; color: #94a3b8; text-align: center;">
            If you didn't create a ForgeLab account, you can ignore this email.<br />
            — The ForgeLab Team
            </p>

        </div>
        </center>
    </body>
    </html>
    """

    email_msg = {
        "message": {
            "subject": "ForgeLab | Verify Your Email",
            "body": {
                "contentType": "HTML",
                "content": html_content,
            },
            "toRecipients": [
                {"emailAddress": {"address": recipient_email}}
            ],
        },
        "saveToSentItems": "false"
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        f"https://graph.microsoft.com/v1.0/users/{sender_email}/sendMail",
        headers=headers,
        json=email_msg
    )

    if response.status_code != 202:
        raise Exception(f"Email failed: {response.text}")




@api_login.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    print(f"Signup request received: {data}")

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

    # Bypass email verification for satyam@gmail.com
    if email == 'satyam@gmail.com':
        new_user.is_verified = True
        print(f"Email verification bypassed for: {email}")

    db.session.add(new_user)
    db.session.commit()
    
    print(f"User created successfully: {email}, is_verified: {new_user.is_verified}")

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
    
    if user:
        print(f"User details - ID: {user.id}, Email: {user.email}, is_verified: {user.is_verified}")
        print(f"Password check result: {check_password_hash(user.password, password)}")

    if not user:
        print("User not found")
        return jsonify({"error": "Invalid username or password"}), 400
    
    # Check if user needs password setup
    needs_password_setup = check_password_hash(user.password, "temp_password_needs_reset")
    if needs_password_setup:
        print("User needs password setup")
        # Send password setup email
        try:
            from .password_recovery import send_password_reset_email_with_graph
            from itsdangerous import URLSafeTimedSerializer
            import os
            
            serializer = URLSafeTimedSerializer(os.getenv('SECRET_KEY'))
            token = serializer.dumps(user.email, salt="password-reset")
            send_password_reset_email_with_graph(user.email, token)
            print(f"Password setup email sent to {user.email}")
        except Exception as e:
            print(f"Error sending password setup email: {e}")
        
        response_data = {
            "success": False,
            "needs_password_setup": True,
            "message": "Please set up your password. A password setup email has been sent to your email address."
        }
        print(f"Returning password setup response: {response_data}")
        return jsonify(response_data), 409
    
    if not check_password_hash(user.password, password):
        print("Invalid password")
        return jsonify({"error": "Invalid username or password"}), 400
    
    if not user.is_verified:
        return {"error": "Please verify your email"}, 403

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


@api_login.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json()
    email = data.get("email")
    
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"success": False, "error": "No user found with this email."}), 404

    token = generate_verification_token(email, purpose="reset_password")
    send_password_reset_email_with_graph(email, token)
    return jsonify({"success": True, "message": "Password reset email sent."})

@api_login.route("/reset-password", methods=["POST"])
def reset_password():
    try:
        data = request.get_json()
        token = data.get("token")
        new_password = data.get("password")

        email = serializer.loads(token, salt="reset_password", max_age=3600)
        if not email:
            return jsonify({"success": False, "error": "Invalid or expired token."}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"success": False, "error": "User not found."}), 404

        user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
        db.session.commit()

        return jsonify({"success": True, "message": "Password updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
def send_password_reset_email_with_graph(recipient_email, token):
    access_token = get_access_token()
    sender_email = os.getenv("SENDER_EMAIL")
    reset_url = f"{os.getenv('DOMAIN')}/reset-password?token={token}"

    html_content = f"""
    <html>
      <body style="margin: 0; padding: 0; background-color: #0f172a; font-family: 'Segoe UI', sans-serif; color: #e5e7eb;">
        <center style="width: 100%; table-layout: fixed; background-color: #0f172a; padding: 40px 0;">
          <div style="max-width: 600px; margin: auto; background-color: #1e1b2e; padding: 30px; border-radius: 12px;">
            
            <!-- Logo -->
            <table role="presentation" width="100%" style="margin-bottom: 30px;">
              <tr>
                <td align="center">
                  <img src="https://www.forgelab.pro/_next/image?url=%2FForgeLabsLogo.png&w=750&q=75&dpl=dpl_6vbAiZYyLAhMyJ4wEbYm3wB84kXi" alt="ForgeLab Logo" style="height: 200px;" />
                </td>
              </tr>
            </table>

            <!-- Title -->
            <h2 style="color: #a78bfa; text-align: center; font-size: 24px; margin: 0 0 20px;">Reset Your Password</h2>
            <p style="font-size: 16px; line-height: 1.6; text-align: center;">
              We received a request to reset your password. Click the button below to create a new one.
              This link is valid for a limited time only.
            </p>

            <!-- Button -->
            <table role="presentation" align="center" cellpadding="0" cellspacing="0" style="margin: 30px auto;">
              <tr>
                <td bgcolor="#111827" style="border-radius: 8px; text-align: center;">
                  <a href="{reset_url}" style="display: inline-block; padding: 14px 28px; font-size: 15px; color: #ffffff; background-color: #111827; border: 1px solid #a78bfa; text-decoration: none; font-weight: 600; border-radius: 8px;">
                    Reset My Password
                  </a>
                </td>
              </tr>
            </table>

            <!-- Fallback Link -->
            <p style="font-size: 14px; color: #cbd5e1; margin-top: 40px;">
              Or copy and paste this link into your browser:
            </p>
            <p style="word-break: break-all;">
              <a href="{reset_url}" style="color: #a78bfa;">{reset_url}</a>
            </p>

            <!-- Footer -->
            <p style="margin-top: 40px; font-size: 14px; color: #94a3b8; text-align: center;">
              If you didn't request a password reset, you can safely ignore this email.<br />
              — The ForgeLab Team
            </p>
          </div>
        </center>
      </body>
    </html>
    """

    email_msg = {
        "message": {
            "subject": "ForgeLab | Reset Your Password",
            "body": {
                "contentType": "HTML",
                "content": html_content,
            },
            "toRecipients": [
                {"emailAddress": {"address": recipient_email}}
            ],
        },
        "saveToSentItems": "false"
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        f"https://graph.microsoft.com/v1.0/users/{sender_email}/sendMail",
        headers=headers,
        json=email_msg
    )

    if response.status_code != 202:
        raise Exception(f"Password reset email failed: {response.text}")



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