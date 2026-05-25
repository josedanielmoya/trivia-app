import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    # Use relative path to avoid issues with special characters in absolute path
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///instance/trivia.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    TRIVIA_API_URL = "https://opentdb.com/api.php"
    TRIVIA_CATEGORIES_URL = "https://opentdb.com/api_category.php"
    CHARTS_DIR = os.path.join(BASE_DIR, "app", "static", "charts")


class DevelopmentConfig(Config):
    DEBUG = True
    # Use in-memory database for development to avoid file permission issues
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(Config):
    DEBUG = False
    WTF_CSRF_ENABLED = True


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
