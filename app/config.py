from pydantic_settings import BaseSettings
from pydantic import EmailStr

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    mail_username: EmailStr
    mail_password: str
    mail_from: EmailStr
    mail_port: int = 587
    mail_server: str = "smtp.gmail.com"
    mail_from_name: str = "FastAPI Login"

    class Config:
        env_file = ".env"

settings = Settings()