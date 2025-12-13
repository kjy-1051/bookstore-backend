
# 📚 Bookstore API (FastAPI)

FastAPI 기반 백엔드 애플리케이션입니다.
JWT 기반 인증/인가(RBAC)를 사용하며, 도서·댓글·평점 관리 및 관리자 전용 API를 제공합니다.

## 🚀 주요 기능

회원가입 / 로그인 (JWT 인증)

도서 조회, 검색, 페이지네이션

댓글 및 평점 CRUD

관리자 전용 API

도서 / 유저 관리

통계 대시보드

헬스체크 API

Swagger(OpenAPI) 문서 제공

## 🌐 배포 정보

Base URL
http://113.198.66.68:10089

Swagger UI
http://113.198.66.68:10089/docs

Health Check
http://113.198.66.68:10089/health


## 실행 방법

### 로컬 실행

pip install -r requirements.txt

alembic upgrade head

python app/seed.py

uvicorn app.main:app --host 0.0.0.0 --port 8080

### 서버 실행 

pm2 start "uvicorn app.main:app --host 0.0.0.0 --port 8080" --name bookstore

pm2 save

## 환경변수 설명 (.env.example)

DB_HOST = MySQL호스트

DB_PORT = MySQL포트

DB_USER = DB 사용자

DB_PASSWORD = DB 비밀번호

DB_NAME = DB 이름

JWT_SECRET = 서명용 비밀키

ACCESS_TOKEN_EXPIRE_MINUTES = 토큰 만료 시간

REDIS_HOST = Redis host 

REDIS_PORT = Redis host

## 인증 플로우 설명

- /auth/login으로 로그인

- ACCESS TOKEN (JWT) 발급

- 이후 API 요청 시: Authorization: Bearer <AccessToken>

- Role 기반 인가(RBAC): ROLE_USER / ROLE_ADMIN

## 역할 / 권한

| API 경로        | USER | ADMIN |
|-----------------|:----:|:-----:|
| `/books`        |  O   |   O   |
| `/comments`     |  O   |   O   |
| `/ratings`      |  O   |   O   |
| `/admin/*`      |  X   |   O   |

## 예제 계정

- ADMIN: admin@example.com / admin1234

- USER: user1@test.com / 1234

## Database Configuration

- Database credentials are managed via `.env`
- Actual values are **excluded** from this public repository
- Access is restricted to an application-specific database

## 주요 엔드포인트

| Method | URL         | 설명         |
| ------ | ----------- | ----------  |
| POST   | /auth/login | 로그인        |
| GET    | /books      | 도서 목록 조회  |
| GET    | /books/{id} | 도서 상세 조회  |
| POST   | /comments   | 댓글 작성      |
| POST   | /ratings    | 평점 등록      |
| GET    | /health     | 헬스체크       |
| GET    | /docs       | Swagger UI   |


## 성능/보안 고려사항

- JWT 기반 인증 및 Role 기반 인가
  
- 입력값 검증 (Pydantic Schema)
  
- 페이지네이션 / 정렬 지원
  
- Redis 사용 가능 구조 (토큰/캐시 확장 고려)
  
- 관리자 API 분리 설계

## 한계 및 개선 계획

- Refresh Token 로테이션 고도화
  
- Redis 기반 토큰 관리 적용
  
- 통계 API 캐싱 최적화
  
- 관리자 대시보드 지표 확장
