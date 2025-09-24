"""
Password Recovery Routes for VTT_Backend
Handles password recovery for users who don't have passwords set
"""

from flask import Blueprint, request, jsonify
from app.models import db
from app.models.user import User
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
import os
from datetime import datetime, timedelta
import requests

api_password_recovery = Blueprint("password_recovery", __name__, url_prefix="")

serializer = URLSafeTimedSerializer(os.getenv('SECRET_KEY'))

def get_access_token():
    """Get Microsoft Graph API access token for sending emails"""
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
    response.raise_for_status()
    return response.json()["access_token"]

def send_password_reset_email_with_graph(recipient_email, token):
    """Send password reset email using Microsoft Graph API"""
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
            <h2 style="color: #a78bfa; text-align: center; font-size: 24px; margin: 0 0 20px;">Set Your Password</h2>
            <p style="font-size: 16px; line-height: 1.6; text-align: center;">
              Welcome to ForgeLab! Your account has been created and you need to set your password to get started.
              Click the button below to create your password.
            </p>

            <!-- Button -->
            <table role="presentation" align="center" cellpadding="0" cellspacing="0" style="margin: 30px auto;">
              <tr>
                <td bgcolor="#111827" style="border-radius: 8px; text-align: center;">
                  <a href="{reset_url}" style="display: inline-block; padding: 14px 28px; font-size: 15px; color: #ffffff; background-color: #111827; border: 1px solid #a78bfa; text-decoration: none; font-weight: 600; border-radius: 8px;">
                    Set My Password
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
              If you didn't create a ForgeLab account, you can safely ignore this email.<br />
              — The ForgeLab Team
            </p>
          </div>
        </center>
      </body>
    </html>
    """

    email_msg = {
        "message": {
            "subject": "ForgeLab | Set Your Password",
            "body": {
                "contentType": "HTML",
                "content": html_content,
            },
            "toRecipients": [
                {"emailAddress": {"address": recipient_email}}
            ],
        },
        "saveToSentItems": "true"  # Save to sent items for future reference
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

@api_password_recovery.route('/check-password-setup', methods=['POST'])
def check_password_setup():
    """Check if user needs to set up password and send recovery email if needed"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({"error": "Email is required"}), 400
        
        # Find user
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Check if password needs to be set (temporary password)
        needs_password_setup = check_password_hash(user.password, "temp_password_needs_reset")
        
        if needs_password_setup:
            # Generate reset token
            token = serializer.dumps(email, salt="password-reset")
            
            try:
                # Send password setup email
                send_password_reset_email_with_graph(email, token)
                return jsonify({
                    "needs_password_setup": True,
                    "message": "Password setup email sent. Please check your email to set your password."
                }), 200
            except Exception as e:
                print(f"Error sending password setup email: {e}")
                return jsonify({
                    "needs_password_setup": True,
                    "message": "Please contact support to set up your password.",
                    "error": "Email sending failed"
                }), 500
        else:
            return jsonify({
                "needs_password_setup": False,
                "message": "Password is already set. Please use the regular login."
            }), 200
            
    except Exception as e:
        print(f"Error in check_password_setup: {e}")
        return jsonify({"error": "Internal server error"}), 500

@api_password_recovery.route('/setup-password', methods=['POST'])
def setup_password():
    """Set up password for users who don't have one"""
    try:
        data = request.get_json()
        token = data.get('token')
        new_password = data.get('password')
        
        if not token or not new_password:
            return jsonify({"error": "Token and password are required"}), 400
        
        # Verify token
        try:
            email = serializer.loads(token, salt="password-reset", max_age=3600)  # 1 hour expiry
        except:
            return jsonify({"error": "Invalid or expired token"}), 400
        
        # Find user
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Update password
        user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
        db.session.commit()
        
        return jsonify({
            "message": "Password set successfully. You can now log in with your new password."
        }), 200
        
    except Exception as e:
        print(f"Error in setup_password: {e}")
        return jsonify({"error": "Internal server error"}), 500

@api_password_recovery.route('/send-password-reset', methods=['POST'])
def send_password_reset():
    """Send password reset email for existing users"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({"error": "Email is required"}), 400
        
        # Find user
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Generate reset token
        token = serializer.dumps(email, salt="password-reset")
        
        try:
            # Send password reset email
            send_password_reset_email_with_graph(email, token)
            return jsonify({
                "message": "Password reset email sent. Please check your email."
            }), 200
        except Exception as e:
            print(f"Error sending password reset email: {e}")
            return jsonify({
                "error": "Failed to send email. Please try again later."
            }), 500
            
    except Exception as e:
        print(f"Error in send_password_reset: {e}")
        return jsonify({"error": "Internal server error"}), 500

@api_password_recovery.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password using token"""
    try:
        data = request.get_json()
        token = data.get('token')
        new_password = data.get('password')
        
        if not token or not new_password:
            return jsonify({"error": "Token and password are required"}), 400
        
        # Verify token
        try:
            email = serializer.loads(token, salt="password-reset", max_age=3600)  # 1 hour expiry
        except:
            return jsonify({"error": "Invalid or expired token"}), 400
        
        # Find user
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Update password
        user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
        db.session.commit()
        
        return jsonify({
            "message": "Password reset successfully. You can now log in with your new password."
        }), 200
        
    except Exception as e:
        print(f"Error in reset_password: {e}")
        return jsonify({"error": "Internal server error"}), 500
