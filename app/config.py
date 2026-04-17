from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000
    environment: str = "production"
    debug: bool = False
    
    app_name: str = "Production AI Agent"
    app_version: str = "1.0.0"
    
    # LLM
    openai_api_key: str = ""
    llm_model: str = "mock-model"
    
    # Security
    agent_api_key: str = "dev-key-change-me"
    rate_limit_per_minute: int = 10
    monthly_budget_usd: float = 10.0
    
    # Storage
    redis_url: str = "redis://localhost:6379/0"
    
settings = Settings()
