from typing import Optional, List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Configuration
    API_KEY: str = "CHANGE_ME_IN_PRODUCTION"  # Required: Set in environment
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    
    # LLM Configuration
    LLM_PROVIDER: str = "anthropic"  # openai, anthropic, or gemini
    
    # Gemini Configuration - Support multiple API keys
    GOOGLE_API_KEY: Optional[str] = None  # Primary key
    GOOGLE_API_KEY_2: Optional[str] = None  # Additional keys for rotation
    GOOGLE_API_KEY_3: Optional[str] = None
    GOOGLE_API_KEY_4: Optional[str] = None
    GEMINI_MODEL: str = "gemini-pro"
    
    def get_gemini_api_keys(self) -> List[str]:
        keys = []
        for key in [self.GOOGLE_API_KEY, self.GOOGLE_API_KEY_2, 
                    self.GOOGLE_API_KEY_3, self.GOOGLE_API_KEY_4]:
            if key and key != "your-google-api-key-here":
                keys.append(key)
        return keys
    
    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    
    # Anthropic Configuration (Claude Haiku 4.5)
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-haiku-4.5-20250110"
    
    # GUVI Configuration
    GUVI_CALLBACK_URL: str = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"
    
    # Response Configuration
    INCLUDE_DEBUG_INFO: bool = False  # Set to True to include detailed debug fields in response
    
    # Session Configuration
    SESSION_TIMEOUT_MINUTES: int = 30
    MAX_MESSAGES_PER_SESSION: int = 50
    
    # Redis Configuration (Optional)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    USE_REDIS: bool = False
    
    # Performance Configuration (OPTIMIZED FOR SPEED)
    CACHE_MAX_SIZE: int = 500  # Increased cache for more hits
    LLM_MAX_TOKENS_DETECTION: int = 1500  # Increased to prevent truncation
    LLM_MAX_TOKENS_RESPONSE: int = 2000   # Increased to prevent truncation
    LLM_TEMPERATURE_DETECTION: float = 0.1
    LLM_TEMPERATURE_RESPONSE: float = 0.7
    LLM_REQUEST_TIMEOUT: int = 5  # Reduced timeout for faster failures
    
    # Rate Limiting Configuration
    FAST_MODE: bool = False  # False = Throttling enabled (production-safe) + Fast fallbacks
    MIN_REQUEST_INTERVAL: float = 12.0  # Minimum seconds between requests (5 req/min) - ignored in FAST_MODE
    DEFAULT_RETRY_DELAY: float = 60.0  # Default cooldown when retry delay not provided
    QUOTA_EXHAUSTED_COOLDOWN: int = 3600  # Cooldown for daily quota exhaustion (1 hour)
    BILLING_ERROR_COOLDOWN: int = 7200  # Cooldown for billing issues (2 hours)
    FAST_MODE_MAX_RETRY_ATTEMPTS: int = 1  # Only try 1 model in fast mode (vs 6 normally)
    USE_INSTANT_FALLBACK: bool = True  # Use instant fallback when providers in cooldown (best of both worlds)
    
    # Detection Configuration (Dynamic Thresholds)
    SCAM_DETECTION_THRESHOLD: float = 0.5  # Minimum confidence to consider as scam
    SCAM_SCORE_THRESHOLD: int = 2  # Minimum total score for scam detection
    LOTTERY_CONFIDENCE_MULTIPLIER: float = 0.3
    BANK_FRAUD_CONFIDENCE_MULTIPLIER: float = 0.25
    UPI_CONFIDENCE_MULTIPLIER: float = 0.3
    PHISHING_CONFIDENCE_MULTIPLIER: float = 0.35
    GENERIC_CONFIDENCE_MULTIPLIER: float = 0.25
    MAX_CONFIDENCE: float = 0.95
    MIN_CONFIDENCE_NOT_SCAM: float = 0.4
    
    # Conversation Configuration
    PERSONA_CHANGE_INTERVAL: int = 5  # Change persona every N messages
    EARLY_STAGE_THRESHOLD: int = 3  # Messages before mid-conversation
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
