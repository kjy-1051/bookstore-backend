from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    class Config:
        env_file = ".env"

settings = Settings()

DATABASE_URL = (
    f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
