import os
from dotenv import load_dotenv

# Load environment variables from .env file at project root if present
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
load_dotenv(dotenv_path)

class Config:
    """Centralized Backend Application Configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-me-in-production')
    
    # Database path configuration
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DEFAULT_DB_PATH = os.path.join(BASE_DIR, 'database', 'waremind.db')
    DATABASE_PATH = os.environ.get('DATABASE_PATH', DEFAULT_DB_PATH)
    
    # Server & Environment
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() in ['true', '1', 't']
    PORT = int(os.environ.get('FLASK_PORT', 5000))
    
    # CORS Configuration
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    # Optional Gemini Integration
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
