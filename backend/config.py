"""
Configuration Module
Loads configuration from environment variables
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration"""
    
    # Flask Configuration
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    HOST = os.getenv('FLASK_HOST', '127.0.0.1')
    PORT = int(os.getenv('FLASK_PORT', 5000))
    
    # Database Configuration
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'database.db')
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
    JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', 24))
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
    
    # Security
    BCRYPT_ROUNDS = int(os.getenv('BCRYPT_ROUNDS', 12))
    
    # ML Model Configuration
    ML_MODEL_PATH = os.getenv('ML_MODEL_PATH', 'risk_model.pkl')
    ML_MIN_TRAINING_SAMPLES = int(os.getenv('ML_MIN_TRAINING_SAMPLES', 10))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'app.log')
    
    @classmethod
    def validate(cls):
        """Validate critical configuration"""
        if cls.JWT_SECRET_KEY == 'dev-secret-key-change-in-production' and cls.FLASK_ENV == 'production':
            raise ValueError("JWT_SECRET_KEY must be changed in production!")
        
        if cls.FLASK_ENV == 'production' and cls.DEBUG:
            raise ValueError("DEBUG must be False in production!")
    
    @classmethod
    def get_database_path(cls):
        """Get absolute path to database"""
        return os.path.abspath(cls.DATABASE_PATH)

# Validate configuration on import
Config.validate()
