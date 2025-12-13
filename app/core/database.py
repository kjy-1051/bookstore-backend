from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

Base = declarative_base()


engine = create_engine(
    f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@127.0.0.1:{settings.DB_PORT}/{settings.DB_NAME}",
    pool_pre_ping=True
)



SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

def get_engine():
    return engine

def get_session_local():
    return SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
