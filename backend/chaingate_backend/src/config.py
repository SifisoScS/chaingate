import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # SQL Server Configuration
    DB_SERVER = os.getenv('DB_SERVER', 'localhost')
    DB_NAME = os.getenv('DB_NAME', 'chaingate')
    DB_USER = os.getenv('DB_USER', '')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_DRIVER = os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')
    
    # Build connection string based on authentication method
    if DB_USER and DB_PASSWORD:
        # SQL Server Authentication
        SQLALCHEMY_DATABASE_URI = f"mssql+pyodbc://{DB_USER}:{DB_PASSWORD}@{DB_SERVER}/{DB_NAME}?driver={DB_DRIVER}"
    else:
        # Windows Authentication
        SQLALCHEMY_DATABASE_URI = f"mssql+pyodbc://@{DB_SERVER}/{DB_NAME}?driver={DB_DRIVER}&trusted_connection=yes"
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Application Settings
    BITCOIN_NETWORK = os.getenv('BITCOIN_NETWORK', 'testnet')
    COMPLIANCE_LEVEL = os.getenv('COMPLIANCE_LEVEL', 'high')
    KYC_REQUIRED = os.getenv('KYC_REQUIRED', 'True').lower() == 'true'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    DB_NAME = 'chaingate_test'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}