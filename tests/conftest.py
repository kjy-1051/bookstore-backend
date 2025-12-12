import pytest
from fastapi.testclient import TestClient
from app.main import app

import pytest
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.user import User
from app.models.book import Book
from datetime import date
from app.core.security import hash_password

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.core.database import get_db

# 테스트 전용 DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
# 또는 완전 격리
# SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    from app.models.user import User
    from app.core.security import hash_password

    db = TestingSessionLocal()

    db.add_all([
        User(
            email="admin@test.com",
            name="Admin",
            role="ADMIN",
            status="ACTIVE",
            hashed_password=hash_password("password123")
        ),
        User(
            email="user1@test.com",
            name="User1",
            role="USER",
            status="ACTIVE",
            hashed_password=hash_password("password123")
        )
    ])

    # 책 seed (이게 핵심)
    db.add(
        Book(
            id=1,  # ← 테스트에서 쓰는 book_id
            title="Test Book",
            isbn="978-0-00-000000-0",
            price=10000,
            publisher="Test Publisher",
            summary="Test summary",
            publication_date=date(2025, 1, 1),
            authors="Tester",
            categories="Test"
        )
    )

    db.commit()
    db.close()


@pytest.fixture(scope="session")
def seed_test_users():
    from app.core.database import SessionLocal, Base, engine
    from app.models.user import User
    from app.core.security import hash_password

    # 🔥 테이블 보장
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    if not db.query(User).filter(User.email == "admin@test.com").first():
        db.add(User(
            email="admin@test.com",
            name="Admin",
            role="ADMIN",
            status="ACTIVE",
            hashed_password=hash_password("password123")
        ))

    if not db.query(User).filter(User.email == "user1@test.com").first():
        db.add(User(
            email="user1@test.com",
            name="User1",
            role="USER",
            status="ACTIVE",
            hashed_password=hash_password("password123")
        ))

    db.commit()
    db.close()


@pytest.fixture(scope="session")
def client():
    return TestClient(app)




@pytest.fixture(scope="session")
def user_token(client):
    """
    일반 USER 토큰
    """
    res = client.post("/auth/login", json={
        "email": "user1@test.com",
        "password": "password123"
    })
    assert res.status_code == 200
    return res.json()["access_token"]


@pytest.fixture(scope="session")
def admin_token(client):
    """
    ADMIN 토큰
    """
    res = client.post("/auth/login", json={
        "email": "admin@test.com",
        "password": "password123"
    })
    assert res.status_code == 200
    return res.json()["access_token"]

