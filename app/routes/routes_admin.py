from flask import Blueprint, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
from app.models.user import User, Subscription, Plan, CharacterArt, Map, Campaign
from app.models import db

load_dotenv()

api_admin = Blueprint("admin", __name__, url_prefix="/admin")
print("ADMIN BLUEPRINT CREATED with prefix: /admin")

def admin_required(f):
    """Decorator to check if user is admin - hardcoded email check against env vars"""
    def decorated_function(*args, **kwargs):
        print(f"ADMIN_REQUIRED DECORATOR CALLED for function: {f.__name__}")
        
        # Get email from query parameter (GET requests) or request body (POST/PUT/DELETE)
        email = None
        if request.method == 'GET':
            email = request.args.get('email')
            print(f"Email from GET query params: {email}")
        else:
            email = request.get_json().get('email') if request.is_json else None
            print(f"Email from request body: {email}")
        
        print(f"Final email value: {email}")
        
        if not email:
            print("No email parameter found")
            return jsonify({"error": "Email parameter required"}), 400
        
        # Get admin email from environment variables
        admin_email = os.getenv('ADMIN_EMAIL', 'admin@forgelab.pro')
        print(f"Environment ADMIN_EMAIL: {admin_email}")
        print(f"Comparing email: '{email}' == '{admin_email}' -> {email == admin_email}")
        
        # Hardcoded admin email check - NO DATABASE QUERY
        if email != admin_email:
            print("Email does not match admin email - access denied")
            return jsonify({"error": "Admin access required"}), 403
        
        print("Email matches admin email - access granted")
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@api_admin.route('/login', methods=['POST'])
def admin_login():
    """Admin login endpoint - completely hardcoded, no DB check needed"""
    print("ADMIN LOGIN ROUTE ACCESSED")
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        print(f"Received email: {email}")
        print(f"Received password: {password}")
        
        if not email or not password:
            print("Missing email or password")
            return jsonify({"error": "Email and password required"}), 400
        
        # Get admin credentials from environment variables
        admin_email = os.getenv('ADMIN_EMAIL', 'admin@forgelab.pro')
        admin_password = os.getenv('ADMIN_PASSWORD', 'Admin123!')
        
        print(f"Environment ADMIN_EMAIL: {admin_email}")
        print(f"Environment ADMIN_PASSWORD: {admin_password}")
        print(f"Comparing email: '{email}' == '{admin_email}' -> {email == admin_email}")
        print(f"Comparing password: '{password}' == '{admin_password}' -> {password == admin_password}")
        
        # Hardcoded admin credentials check - NO DATABASE QUERY
        if email != admin_email or password != admin_password:
            print("Admin credentials mismatch")
            return jsonify({"error": "Invalid admin credentials"}), 401
        
        print("Admin credentials match! Returning success")
        
        # Admin credentials are valid - return success with admin flag
        # No need to check if user exists in database
        response_data = {
            "success": True,
            "message": "Admin login successful",
            "username": email,
            "admin": True,  # This tells frontend user is admin
            "is_verified": True,  # Admin is always verified
            "has_subscription": True  # Admin always has access
        }
        print(f"📤 Sending response: {response_data}")
        return jsonify(response_data), 200
        
    except Exception as e:
        print(f"💥 Exception in admin login: {str(e)}")
        return jsonify({"error": str(e)}), 500

@api_admin.route('/logout', methods=['POST'])
def admin_logout():
    """Admin logout endpoint - validate admin and return success"""
    print("ADMIN LOGOUT ROUTE ACCESSED")
    try:
        data = request.get_json()
        email = data.get('email')
        
        print(f"Received email for logout: {email}")
        
        if not email:
            print("No email provided for logout")
            return jsonify({"error": "Email required for logout"}), 400
        
        # Verify this is actually an admin user
        admin_email = os.getenv('ADMIN_EMAIL', 'admin@forgelab.pro')
        if email != admin_email:
            print("Non-admin user attempting to access admin logout")
            return jsonify({"error": "Admin access required"}), 403
        
        print("Admin logout successful")
        return jsonify({
            "success": True, 
            "message": "Admin logout successful"
        }), 200
        
    except Exception as e:
        print(f"💥 Exception in admin logout: {str(e)}")
        return jsonify({"error": str(e)}), 500

@api_admin.route('/check-auth', methods=['GET'])
def check_admin_auth():
    """Check if admin is authenticated - hardcoded check against env vars"""
    print("ADMIN CHECK-AUTH ROUTE ACCESSED")
    email = request.args.get('email')
    
    print(f"Received email parameter: {email}")
    
    if not email:
        print("No email parameter provided")
        return jsonify({"authenticated": False, "admin": False}), 400
    
    # Get admin email from environment variables
    admin_email = os.getenv('ADMIN_EMAIL', 'admin@forgelab.pro')
    print(f"Environment ADMIN_EMAIL: {admin_email}")
    print(f"Comparing email: '{email}' == '{admin_email}' -> {email == admin_email}")
    
    # Simple hardcoded check - NO DATABASE QUERY
    if email == admin_email:
        print("Email matches admin email! Returning authenticated")
        response_data = {
            "authenticated": True,
            "username": email,
            "admin": True  # This tells frontend user is admin
        }
        print(f"Sending response: {response_data}")
        return jsonify(response_data), 200
    
    print("Email does not match admin email")
    return jsonify({"authenticated": False, "admin": False}), 401

@api_admin.route('/stats', methods=['GET'])
def get_admin_stats():
    """Get admin dashboard statistics"""
    print("🔍 ADMIN STATS ROUTE ACCESSED")
    try:
        # Total users count
        total_users = User.query.count()
        
        # Total subscribed users (active, non-Free plans only)
        subscribed_users = (
            User.query
            .join(Subscription)
            .join(Plan, Subscription.plan_id == Plan.id)
            .filter(Subscription.status == 'active', Plan.name != 'Free')
        ).count()
        
        # Total campaigns generated
        total_campaigns = Campaign.query.count()
        
        # Total maps created
        total_maps = Map.query.count()
        
        # Total characters created
        total_characters = CharacterArt.query.count()
        
        stats = {
            "total_users": total_users,
            "subscribed_users": subscribed_users,
            "total_campaigns": total_campaigns,
            "total_maps": total_maps,
            "total_characters": total_characters
        }
        
        print(f"📊 Stats calculated: {stats}")
        return jsonify(stats), 200
        
    except Exception as e:
        print(f"💥 Exception in get_admin_stats: {str(e)}")
        return jsonify({"error": str(e)}), 500

@api_admin.route('/dashboard/subscribed-users', methods=['GET'])
def get_subscribed_users():
    """Get all subscribed users with pagination for dashboard"""
    print("🔍 DASHBOARD SUBSCRIBED USERS ROUTE ACCESSED")
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '', type=str)
        
        # Query subscribed users (active, non-Free plans only)
        query = (
            User.query
            .join(Subscription)
            .join(Plan, Subscription.plan_id == Plan.id)
            .filter(Subscription.status == 'active', Plan.name != 'Free')
        )
        
        # Add search filter if provided
        if search:
            query = query.filter(
                db.or_(
                    User.username.ilike(f'%{search}%'),
                    User.email.ilike(f'%{search}%'),
                    User.first_name.ilike(f'%{search}%'),
                    User.last_name.ilike(f'%{search}%')
                )
            )
        
        # Paginate results
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        users = []
        for user in pagination.items:
            subscription = Subscription.query.filter_by(user_id=user.id, status='active').join(Plan).filter(Plan.name != 'Free').first()
            plan = Plan.query.get(subscription.plan_id) if subscription else None
            
            users.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_verified': user.is_verified,
                'subscription': {
                    'plan_name': plan.name if plan else 'Unknown',
                    'status': subscription.status if subscription else 'Unknown',
                    'current_period_end': subscription.current_period_end.isoformat() if subscription and subscription.current_period_end else None
                } if subscription else None
            })
        
        return jsonify({
            'success': True,
            'users': users,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        print(f"💥 Exception in get_subscribed_users: {str(e)}")
        return jsonify({"error": str(e)}), 500

@api_admin.route('/dashboard/maps', methods=['GET'])
def get_dashboard_maps():
    """Get all maps with pagination for dashboard"""
    print("🔍 DASHBOARD MAPS ROUTE ACCESSED")
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 12, type=int)
        search = request.args.get('search', '', type=str)
        
        # Query maps
        query = Map.query
        
        # Add search filter if provided
        if search:
            query = query.filter(
                db.or_(
                    Map.description.ilike(f'%{search}%'),
                    Map.style.ilike(f'%{search}%'),
                    Map.tone.ilike(f'%{search}%')
                )
            )
        
        # Paginate results
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        maps = []
        for map_item in pagination.items:
            # Get user info from username
            user = User.query.filter_by(username=map_item.username).first()
            maps.append({
                'id': map_item.id,
                'image_url': map_item.image_url,
                'description': map_item.description,
                'style': map_item.style,
                'tone': map_item.tone,
                'created_at': map_item.created_at.isoformat() if map_item.created_at else None,
                'user': {
                    'username': user.username if user else map_item.username,
                    'email': user.email if user else 'Unknown'
                } if user else {'username': map_item.username, 'email': 'Unknown'}
            })
        
        return jsonify({
            'success': True,
            'maps': maps,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        print(f"💥 Exception in get_dashboard_maps: {str(e)}")
        return jsonify({"error": str(e)}), 500

@api_admin.route('/dashboard/characters', methods=['GET'])
def get_dashboard_characters():
    """Get all characters with pagination for dashboard"""
    print("🔍 DASHBOARD CHARACTERS ROUTE ACCESSED")
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 12, type=int)
        search = request.args.get('search', '', type=str)
        
        # Query characters
        query = CharacterArt.query
        
        # Add search filter if provided
        if search:
            query = query.filter(
                db.or_(
                    CharacterArt.description.ilike(f'%{search}%'),
                    CharacterArt.style.ilike(f'%{search}%'),
                    CharacterArt.tags.any(lambda tag: tag.name.ilike(f'%{search}%'))
                )
            )
        
        # Paginate results
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        characters = []
        for character in pagination.items:
            # Get user info from username
            user = User.query.filter_by(username=character.username).first()
            # Get tags
            tags = [tag.name for tag in character.tags] if character.tags else []
            
            characters.append({
                'id': character.id,
                'image_url': character.image_url,
                'description': character.description,
                'style': character.style,
                'tags': tags,
                'created_at': character.created_at.isoformat() if character.created_at else None,
                'user': {
                    'username': user.username if user else character.username,
                    'email': user.email if user else 'Unknown'
                } if user else {'username': character.username, 'email': 'Unknown'}
            })
        
        return jsonify({
            'success': True,
            'characters': characters,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        print(f"💥 Exception in get_dashboard_characters: {str(e)}")
        return jsonify({"error": str(e)}), 500

@api_admin.route('/users', methods=['GET'])
@admin_required
def get_users():
    """Get paginated list of users with search functionality"""
    print("🔍 GET_USERS ROUTE ACCESSED")
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '', type=str)
        
        print(f"📊 Query params - page: {page}, per_page: {per_page}, search: '{search}'")
        
        # Build query
        query = User.query
        
        # Apply search filter if provided
        if search:
            search_filter = f"%{search}%"
            print(f"🔍 Applying search filter: {search_filter}")
            query = query.filter(
                db.or_(
                    User.username.ilike(search_filter),
                    User.email.ilike(search_filter),
                    User.first_name.ilike(search_filter),
                    User.last_name.ilike(search_filter)
                )
            )
            print(f"🔍 Search filter applied, query built")
        else:
            print("🔍 No search term provided, showing all users")
        
        # Get paginated results
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        print(f"📊 Pagination results - total: {pagination.total}, pages: {pagination.pages}, current page: {pagination.page}")
        print(f"📊 Users found: {len(pagination.items)}")
        
        # Format user data
        users = []
        for user in pagination.items:
            # Get subscription info
            subscription_info = None
            if user.subscription:
                plan = Plan.query.get(user.subscription.plan_id)
                subscription_info = {
                    "status": user.subscription.status,
                    "plan_name": plan.name if plan else "Unknown",
                    "created_at": user.subscription.created_at.isoformat() if user.subscription.created_at else None,
                    "usage_count": user.subscription.usage_count
                }
            
            users.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_verified": user.is_verified,
                "is_subaccount": user.is_subaccount,
                "subscription": subscription_info
            })
        
        response_data = {
            "success": True,
            "users": users,
            "pagination": {
                "page": pagination.page,
                "pages": pagination.pages,
                "per_page": pagination.per_page,
                "total": pagination.total,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev
            }
        }
        
        print(f"📤 Sending response with {len(users)} users")
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api_admin.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """Delete a user and all associated data"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                "success": False,
                "error": "User not found"
            }), 404
        
        # Delete associated data
        # Delete characters
        CharacterArt.query.filter_by(username=user.username).delete()
        
        # Delete maps
        Map.query.filter_by(username=user.username).delete()
        
        # Delete campaigns
        Campaign.query.filter_by(username=user.username).delete()
        
        # Delete subscription if exists
        if user.subscription:
            db.session.delete(user.subscription)
        
        # Delete the user
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "User and associated data deleted successfully"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api_admin.route('/users/<int:user_id>/details', methods=['GET'])
@admin_required
def get_user_details(user_id):
    """Get detailed information about a specific user"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                "success": False,
                "error": "User not found"
            }), 404
        
        # Get user statistics
        character_count = CharacterArt.query.filter_by(username=user.username).count()
        map_count = Map.query.filter_by(username=user.username).count()
        campaign_count = Campaign.query.filter_by(username=user.username).count()
        
        # Get subscription details
        subscription_details = None
        if user.subscription:
            plan = Plan.query.get(user.subscription.plan_id)
            subscription_details = {
                "id": user.subscription.id,
                "stripe_subscription_id": user.subscription.stripe_subscription_id,
                "status": user.subscription.status,
                "plan": {
                    "id": plan.id if plan else None,
                    "name": plan.name if plan else "Unknown",
                    "price": plan.price if plan else 0,
                    "interval": plan.interval if plan else "unknown"
                },
                "current_period_start": user.subscription.current_period_start.isoformat() if user.subscription.current_period_start else None,
                "current_period_end": user.subscription.current_period_end.isoformat() if user.subscription.current_period_end else None,
                "usage_count": user.subscription.usage_count,
                "created_at": user.subscription.created_at.isoformat() if user.subscription.created_at else None,
                "updated_at": user.subscription.updated_at.isoformat() if user.subscription.updated_at else None
            }
        
        return jsonify({
            "success": True,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_verified": user.is_verified,
                "is_subaccount": user.is_subaccount,
                "stripe_customer_id": user.stripe_customer_id,
                "parent_username": user.parent_username,
                "statistics": {
                    "characters_created": character_count,
                    "maps_created": map_count,
                    "campaigns_created": campaign_count
                },
                "subscription": subscription_details
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
