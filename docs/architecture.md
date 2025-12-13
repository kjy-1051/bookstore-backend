📄 docs/architecture.md

애플리케이션 구조 개요

1. 아키텍처 개요

본 프로젝트는 FastAPI 기반 계층형 아키텍처를 따른다.
API Router
   ↓
Service Layer
   ↓
Repository(DB Session)

2. 계층별 역할

2.1 Router

요청/응답 처리
인증/인가 의존성 적용
HTTP 상태 코드 반환
예:
/books
/admin/books
/auth/login

2.2 Service Layer

비즈니스 로직 담당
권한 검증
예외 처리

2.3 Model / Schema

SQLAlchemy ORM 모델
Pydantic Schema로 요청/응답 검증

3. 공통 모듈

3.1 인증 / 보안

JWT 기반 인증
RBAC(Role Based Access Control)
관리자 전용 의존성 분리

3.2 예외 처리

CustomException 기반 통일된 오류 응답
에러 코드 열거형 관리

3.3 문서화

Swagger(OpenAPI) 자동 생성
요청/응답 및 오류 예시 포함

4. 구조 선택 이유

책임 분리로 유지보수 용이
테스트 및 확장성 고려
과제 요구사항 충족 및 실제 서비스 구조 반영