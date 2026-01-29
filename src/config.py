"""
Configuration management for TikTok Ads AI Agent
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # LLM Configuration
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
    
    # TikTok OAuth Configuration
    TIKTOK_APP_ID: Optional[str] = os.getenv("TIKTOK_APP_ID")
    TIKTOK_APP_SECRET: Optional[str] = os.getenv("TIKTOK_APP_SECRET")
    TIKTOK_REDIRECT_URI: str = os.getenv("TIKTOK_REDIRECT_URI", "http://localhost:8080/callback")
    
    # API Configuration
    TIKTOK_API_BASE_URL: str = os.getenv(
        "TIKTOK_API_BASE_URL", 
        "https://business-api.tiktok.com/open_api/v1.3"
    )
    
    # Mode Configuration
    USE_MOCK_API: bool = os.getenv("USE_MOCK_API", "false").lower() == "true"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # OAuth Server Configuration
    OAUTH_SERVER_HOST: str = os.getenv("OAUTH_SERVER_HOST", "localhost")
    OAUTH_SERVER_PORT: int = int(os.getenv("OAUTH_SERVER_PORT", "8080"))
    
    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent
    CREDENTIALS_FILE: Path = BASE_DIR / "credentials.json"
    
    @classmethod
    def validate(cls) -> list[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        if not cls.USE_MOCK_API:
            # Validate TikTok credentials
            if not cls.TIKTOK_APP_ID:
                errors.append("TIKTOK_APP_ID not set in .env")
            if not cls.TIKTOK_APP_SECRET:
                errors.append("TIKTOK_APP_SECRET not set in .env")
        
        # Validate LLM configuration
        if not cls.OPENAI_API_KEY and not cls.ANTHROPIC_API_KEY:
            errors.append("Either OPENAI_API_KEY or ANTHROPIC_API_KEY must be set")
        
        return errors
    
    @classmethod
    def get_llm_provider(cls) -> str:
        """Determine which LLM provider to use"""
        if cls.OPENAI_API_KEY:
            return "openai"
        elif cls.ANTHROPIC_API_KEY:
            return "anthropic"
        else:
            raise ValueError("No LLM API key configured")
    
    @classmethod
    def print_config(cls):
        """Print current configuration (excluding secrets)"""
        print("\n" + "="*60)
        print("CONFIGURATION")
        print("="*60)
        print(f"LLM Provider: {cls.get_llm_provider()}")
        print(f"Model: {cls.OPENAI_MODEL if cls.get_llm_provider() == 'openai' else cls.ANTHROPIC_MODEL}")
        print(f"Mock API Mode: {cls.USE_MOCK_API}")
        print(f"Debug Mode: {cls.DEBUG}")
        print(f"OAuth Server: {cls.OAUTH_SERVER_HOST}:{cls.OAUTH_SERVER_PORT}")
        print("="*60 + "\n")


# Business Rules Configuration
class BusinessRules:
    """Business rules for ad campaign creation"""
    
    # Campaign name rules
    CAMPAIGN_NAME_MIN_LENGTH = 3
    
    # Ad text rules
    AD_TEXT_MAX_LENGTH = 100
    
    # Objectives
    VALID_OBJECTIVES = ["Traffic", "Conversions"]
    
    # CTAs
    VALID_CTAS = [
        "LEARN_MORE",
        "SHOP_NOW", 
        "SIGN_UP",
        "DOWNLOAD",
        "BOOK_NOW",
        "CONTACT_US",
        "GET_QUOTE",
        "APPLY_NOW",
        "WATCH_MORE"
    ]
    
    # Music rules
    MUSIC_REQUIRED_FOR = ["Conversions"]
    MUSIC_OPTIONAL_FOR = ["Traffic"]
    
    @classmethod
    def requires_music(cls, objective: str) -> bool:
        """Check if objective requires music"""
        return objective in cls.MUSIC_REQUIRED_FOR
    
    @classmethod
    def allows_no_music(cls, objective: str) -> bool:
        """Check if objective allows no music"""
        return objective in cls.MUSIC_OPTIONAL_FOR