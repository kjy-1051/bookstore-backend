from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    #REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    class Config:
        env_file = ".env"

settings = Settings()

