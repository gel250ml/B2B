import os
from pathlib import Path
from dotenv import load_dotenv

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
MODERATION_URL = os.getenv("MODERATION_URL")
B2B_TO_MOD_KEY = os.getenv("B2B_TO_MOD_KEY")
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)