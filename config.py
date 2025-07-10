# Ray/config.py
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

class Config:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    MAX_RESPONSE_TOKENS = 150
    TEMPERATURE = 0.3
    CACHE_EXPIRY_HOURS = 1