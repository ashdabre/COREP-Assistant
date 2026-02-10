
import os
from typing import List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings(BaseModel):
    # API Settings
    APP_NAME: str = "COREP Regulatory Assistant"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Grok API Settings
    GROK_API_KEY: str = Field(default="", env="GROK_API_KEY")
    GROK_API_BASE_URL: str = Field(default="https://api.x.ai/v1", env="GROK_API_BASE_URL")
    LLM_MODEL: str = Field(default="grok-beta", env="LLM_MODEL")
    
    # Embeddings
    USE_OPENAI_EMBEDDINGS: bool = Field(default=False, env="USE_OPENAI_EMBEDDINGS")
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    EMBEDDING_MODEL: str = Field(default="all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    
    # Database
    DATABASE_URL: str = Field(default="sqlite:///./data/regulatory.db", env="DATABASE_URL")
    EMBEDDINGS_DB_PATH: str = Field(default="./data/embeddings", env="EMBEDDINGS_DB_PATH")
    
    # COREP Settings - Handle as string and parse
    ALLOWED_TEMPLATES_STR: str = Field(default="C_01.00,C_02.00", env="ALLOWED_TEMPLATES")
    
    @property
    def ALLOWED_TEMPLATES(self) -> List[str]:
        """Parse comma-separated string to list."""
        if not self.ALLOWED_TEMPLATES_STR:
            return ["C_01.00", "C_02.00"]
        return [t.strip() for t in self.ALLOWED_TEMPLATES_STR.split(",") if t.strip()]
    
    DEFAULT_TEMPLATE: str = Field(default="C_01.00", env="DEFAULT_TEMPLATE")
    
    # Retrieval Settings
    MAX_RETRIEVAL_RESULTS: int = Field(default=5, env="MAX_RETRIEVAL_RESULTS")
    SIMILARITY_THRESHOLD: float = Field(default=0.7, env="SIMILARITY_THRESHOLD")
    
    # LLM Settings
    LLM_TEMPERATURE: float = Field(default=0.1, env="LLM_TEMPERATURE")
    MAX_TOKENS: int = Field(default=2000, env="MAX_TOKENS")
    
    # File paths
    DATA_DIR: str = Field(default="./data", env="DATA_DIR")
    LOGS_DIR: str = Field(default="./logs", env="LOGS_DIR")

# Create settings instance
settings = Settings()