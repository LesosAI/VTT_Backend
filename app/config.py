import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    DEBUG = True

    # Check if we should use SQLite for development
    if os.getenv('USE_SQLITE', 'false').lower() == 'true':
        # Use SQLite for development
        SQLALCHEMY_DATABASE_URI = "sqlite:///dev_database.db"
        print("Using SQLite database for development")
    else:
        # Use PostgreSQL
        database_url = os.environ.get('SQLALCHEMY_DATABASE_URI')
        if database_url and database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        SQLALCHEMY_DATABASE_URI = database_url
        print("Using PostgreSQL database")

class ProductionConfig(Config):
    DEBUG = False
    # SQLALCHEMY_DATABASE_URI for production DB