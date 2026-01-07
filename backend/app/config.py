from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./automatic_switch.db"
    
    # Serial Defaults
    SERIAL_BAUDRATE: int = 9600
    SERIAL_TIMEOUT: int = 10
    
    # Execution
    DEFAULT_PARALLELISM: int = 4
    
    # Security
    API_PASSCODE: Optional[str] = None
    CORS_ORIGINS: List[str] = ["*"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "text" # "text" or "json"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

settings = Settings()
