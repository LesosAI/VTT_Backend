#!/usr/bin/env python3
"""
Run Flask app with SQLite database for development
"""
import os
import sys

# Set environment variable to use SQLite
os.environ['USE_SQLITE'] = 'false'

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app

if __name__ == "__main__":
    app = create_app()
    
    print("Starting Flask app with SQLite database...")
    print("Database file: dev_database.db")
    print("Access the app at: http://localhost:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=True) 