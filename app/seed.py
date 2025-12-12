import random
from faker import Faker
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.book import Book
from app.models.comment import Comment
from app.models.rating import Rating
from app.core.security import hash_password

fake = Faker("ko_KR")

def seed():
    db: Session = SessionLocal()

    print("\n⚠ 기존 데이터 전부 삭제 중...")

    # DROP ALL + 다시 생성
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    print("📌 DB 초기화 완료, 데이터 생성 시작...\n")

    # ---------------------- 1) 관리자 계정 ----------------------
    admin = User(
        email="admin@example.com",
        hashed_password=hash_password("admin1234"),
        name="관리자",
        phone="010-0000-0000",
        address="서울 특별시",
        role="admin",
        status="ACTIVE"
    )
    db.add(admin)

    # ---------------------- 2) 일반 유저 다수 생성 ----------------------
    users = []
    for _ in range(29):   # 총 30명
        user = User(
            email=fake.unique.email(),
            hashed_password=hash_password("test1234"),
            name=fake.name(),
            phone=fake.phone_number(),
            address=fake.address(),
            role="user",
            status="ACTIVE"
        )
        users.append(user)
        db.add(user)
    db.commit()
    print("✔ Users 30명 생성 완료")

    # ---------------------- 3) Books 생성 ----------------------
    books = []
    for _ in range(50):   # 50권
        book = Book(
            isbn=fake.unique.isbn13(),
            title=fake.sentence(nb_words=3),
            price=random.randint(7000, 45000),
            publisher=fake.company(),
            summary=fake.text(max_nb_chars=60),
            publication_date=fake.date_between(start_date="-3y", end_date="today"),
            authors=",".join([fake.name() for _ in range(random.randint(1,3))]),
            categories=",".join(random.sample(
                ["IT","소설","과학","철학","자기계발","역사","경제","예술"],
                k=random.randint(1,3)
            ))
        )
        books.append(book)
        db.add(book)
    db.commit()
    print("✔ Books 50권 생성 완료")

    # ---------------------- 4) Comments 100개 ----------------------
    comments = []
    for _ in range(100):
        comments.append(
            Comment(
                user_id=random.choice(users).id,
                book_id=random.choice(books).id,
                content=fake.sentence()
            )
        )
    db.bulk_save_objects(comments)
    db.commit()
    print("✔ Comments 100개 생성 완료")

    # ---------------------- 5) Ratings (충돌 방지 Upsert형 생성) ----------------------
    rating_set = set()
    ratings = []

    while len(ratings) < 100:
        u = random.choice(users).id
        b = random.choice(books).id
        key = (u, b)

        if key in rating_set:
            continue  # 중복 평점 방지

        ratings.append(
            Rating(
                user_id=u,
                book_id=b,
                score=random.randint(1,5)
            )
        )
        rating_set.add(key)

    db.bulk_save_objects(ratings)
    db.commit()
    db.close()

    print("\n🔥 SEEDING 완료! DB에 200+건 자동 생성됨.\n")



if __name__ == "__main__":
    seed()
