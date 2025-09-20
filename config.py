import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DEVIN_API_KEY = os.getenv("DEVIN_API_KEY")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") 
    DEVIN_API_BASE = os.getenv("DEVIN_API_BASE", "https://api.devin.ai/v1")
    
    @classmethod
    def validate(cls):
        if not cls.DEVIN_API_KEY or cls.DEVIN_API_KEY.startswith("placeholder"):
            raise ValueError("DEVIN_API_KEY environment variable is required. Please set a valid Devin API key in your .env file.")
        if not cls.GITHUB_TOKEN or cls.GITHUB_TOKEN.startswith("placeholder"):
            raise ValueError("GITHUB_TOKEN environment variable is required. Please set a valid GitHub token in your .env file.")
    
    @classmethod
    def has_valid_credentials(cls):
        """Check if valid credentials are available without raising exceptions"""
        return (cls.DEVIN_API_KEY and not cls.DEVIN_API_KEY.startswith("placeholder") and
                cls.GITHUB_TOKEN and not cls.GITHUB_TOKEN.startswith("placeholder"))
