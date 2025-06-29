# config.py
import os
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # This tells Pydantic to load variables from a .env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
    # Database
    database_url: str = "sqlite:///./app.db"
    
    # Google GenAI - Using Field to map GEMINI_API_KEY environment variable
    google_api_key: str = Field(default="", env="GEMINI_API_KEY")
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

# Cost & ROI Configuration
# Cost per invoice processed by the AI agent
AGENT_COST_PER_INVOICE: float = 0.90
# Estimated monthly infrastructure cost (e.g., servers, database)
INFRA_COST_MONTHLY: float = 50.00
# Estimated average time in hours to manually process an invoice with an exception
AVG_MANUAL_HANDLING_TIME_HOURS: float = 0.25  # e.g., 15 minutes
# Estimated average hourly wage for an AP clerk
AVG_AP_CLERK_HOURLY_WAGE: float = 25.00 