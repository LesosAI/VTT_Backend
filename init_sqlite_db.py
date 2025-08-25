#!/usr/bin/env python3
"""
Initialize SQLite database with sample data for development
"""
import os
import sys
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db
from app.models.user import User, Plan, Subscription

def init_sqlite_database():
    """Initialize SQLite database with sample data"""
    app = create_app()
    
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        
        print("Creating sample plans...")
        plans = [
            {
                "name": "Free",
                "description": "Basic features to get you started",
                "price": 0.00,
                "stripe_price_id": "",
                "interval": "month",
                "usage_limit": 1
            },
            {
                "name": "Game Master Monthly",
                "description": "Full access to all Game Master features",
                "price": 12.00,
                "stripe_price_id": "price_1R64E502khdf3R0A1tvUHNbt",
                "interval": "month",
                "usage_limit": None
            },
            {
                "name": "Game Master Yearly",
                "description": "Full access to all Game Master features",
                "price": 108.00,
                "stripe_price_id": "price_1R64E502khdf3R0AbLwQdeAA",
                "interval": "year",
                "usage_limit": None
            },
        ]

        for plan_data in plans:
            existing_plan = Plan.query.filter_by(
                name=plan_data['name'], 
                interval=plan_data['interval']
            ).first()
            if not existing_plan:
                new_plan = Plan(
                    name=plan_data['name'],
                    description=plan_data['description'],
                    price=plan_data['price'],
                    stripe_price_id=plan_data['stripe_price_id'],
                    interval=plan_data['interval'],
                    usage_limit=plan_data.get('usage_limit')
                )
                db.session.add(new_plan)
        
        print("Creating sample user...")
        # Create a test user
        test_user = User.query.filter_by(username="testuser").first()
        if not test_user:
            test_user = User(
                username="testuser",
                email="test@example.com",
                password=generate_password_hash("password123", method='pbkdf2:sha256'),
                is_verified=True
            )
            db.session.add(test_user)
            db.session.flush()  # Get the user ID
            
            # Get the Game Master Monthly plan
            game_master_plan = Plan.query.filter_by(name="Game Master Monthly").first()
            
            if game_master_plan:
                # Create a subscription for the test user
                subscription = Subscription(
                    user_id=test_user.id,
                    stripe_subscription_id="test_subscription",
                    status="active",
                    plan_id=game_master_plan.id,
                    current_period_start=datetime.utcnow(),
                    current_period_end=datetime.utcnow() + timedelta(days=30),
                    usage_count=0
                )
                db.session.add(subscription)
        
        db.session.commit()
        print("Database initialized successfully!")
        print(f"Test user: testuser")
        print(f"Test password: password123")
        print(f"Database file: dev_database.db")

if __name__ == "__main__":
    init_sqlite_database() 