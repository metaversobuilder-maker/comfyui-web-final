from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database - SQLite para desarrollo
    database_url: str = "sqlite+aiosqlite:///./comfyui.db"
    database_url_sync: str = "sqlite:///./comfyui.db"
    
    # App
    app_name: str = "ComfyUI Web API"
    debug: bool = True
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
