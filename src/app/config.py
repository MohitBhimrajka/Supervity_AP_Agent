# config.py
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # This tells Pydantic to load variables from a .env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    
    # Database
    database_url: str = "sqlite:///./app.db"
    
    # Google GenAI
    google_api_key: str = os.getenv("GEMINI_API_KEY", "")
    # Updated model name for the new Gemini API
    gemini_model_name: str = "gemini-2.5-flash"

settings = Settings()

# The percentage variance allowed for a unit price mismatch between PO and Invoice.
# 5.0 means a 5% tolerance.
PRICE_TOLERANCE_PERCENT = 5.0

# The percentage variance allowed for a quantity mismatch between GRN and Invoice.
QUANTITY_TOLERANCE_PERCENT = 0.0  # Must be an exact match

# Parallel processing configuration
# Number of worker threads for parallel document processing
PARALLEL_WORKERS = 9 