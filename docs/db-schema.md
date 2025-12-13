📄 docs/db-schema.md

데이터베이스 스키마 정의

1. 개요

본 프로젝트는 관계형 데이터베이스(MySQL)를 사용하며,
도서–사용자–댓글–평점 간의 관계를 명확히 표현하는 구조로 설계되었다.

2. 주요 테이블

2.1 users

컬럼	타입	설명
id	BIGINT	PK
email	VARCHAR	사용자 이메일 (Unique)
password	VARCHAR	해시된 비밀번호
role	ENUM	USER / ADMIN
status	ENUM	ACTIVE / INACTIVE
created_at	DATETIME	생성 시각

2.2 books

컬럼	타입	설명
id	BIGINT	PK
isbn	VARCHAR	ISBN
title	VARCHAR	도서 제목
price	INT	가격
publisher	VARCHAR	출판사
publication_date	DATE	출판일

2.3 comments

컬럼	타입	설명
id	BIGINT	PK
user_id	BIGINT	FK → users
book_id	BIGINT	FK → books
content	TEXT	댓글 내용
created_at	DATETIME	작성 시각

2.4 ratings

컬럼	타입	설명
id	BIGINT	PK
user_id	BIGINT	FK → users
book_id	BIGINT	FK → books
score	INT	평점 (1~5)

사용자 1명당 도서 1권에 평점 1개 제한
(user_id, book_id) 유니크 제약 조건 적용

3. 관계 요약

User : Book = N : M
→ Comment, Rating 테이블로 관계 분리
Book 삭제 시 Comment / Rating 연쇄 삭제 (CASCADE)