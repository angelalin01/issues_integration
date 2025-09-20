import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DEVIN_API_KEY = os.getenv("DEVIN_API_KEY")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") 
    DEVIN_API_BASE = os.getenv("DEVIN_API_BASE", "https://api.devin.ai/v1")
    
    @classmethod
    def validate(cls):
        if not cls.DEVIN_API_KEY:
            raise ValueError("DEVIN_API_KEY environment variable is required")
        if not cls.GITHUB_TOKEN:
            raise ValueError("GITHUB_TOKEN environment variable is required")
