import os
from dotenv import load_dotenv
from datetime import timedelta
load_dotenv()

class Config:
    # Configuración base
    SECRET_KEY = os.getenv('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Base de datos
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or 'sqlite:///app.db'

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = "memory://"
    RATELIMIT_DEFAULT = "100 per hour"
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    #WhatsApp API
    ACCESS_TOKEN = "EAAnWZB7oJeF0BPlkfgpGiMMZAV7UG4KqH2roI4mnvqcZAbN9viCqZBtHKFtMudYZCSP5WxG80smnT1dOpua3Yi8f9WBuvu99VUIORfUCydLSD53ecJtmbZBwY4WcuqKlGnxJtQpUeQsK0Jt95XQAlCt8RhYQ6YoUJ7aCe54vjtW7BwDvd43oQok753m8ZCjigZDZD"
    VERIFY_TOKEN = "202510"
    PHONE_NUMBER_ID = "833447706510609"