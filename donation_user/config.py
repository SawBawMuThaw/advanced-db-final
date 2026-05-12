import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the same directory as this script
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

class Settings:
    # Database
    DB_SERVER = os.getenv("DB_SERVER")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    
    # JWT
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "RS256")
    JWT_EXPIRE_MIN = int(os.getenv("JWT_EXPIRE_MIN", "60"))
    JWT_PRIVATE_KEY_PATH = os.getenv("JWT_PRIVATE_KEY_PATH", "private_key.pem")
    JWT_PUBLIC_KEY_PATH = os.getenv("JWT_PUBLIC_KEY_PATH", "public_key.pem")
    
    # Stripe
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    
    @classmethod
    def get_jwt_keys(cls):
        with open(cls.JWT_PRIVATE_KEY_PATH, "r") as f:
            private_key = f.read()
        with open(cls.JWT_PUBLIC_KEY_PATH, "r") as f:
            public_key = f.read()
        return private_key, public_key

settings = Settings()