# Notify API 구조 문서

이 문서는 `notify-api` 저장소의 현재 구조와 운영 반영 흐름을 빠르게 파악하기 위한 요약 문서입니다.

## 1) 저장소 구조

```text
notify-api/
├─ app/                      # FastAPI 애플리케이션 본체
│  ├─ main.py                # API 라우트(/health, /notify*)
│  ├─ models.py              # 요청/응답 스키마 및 검증
│  ├─ config.py              # 환경변수 로딩 + 이메일 라우팅 규칙
│  ├─ channels/
│  │  ├─ telegram.py         # Telegram 전송 채널
│  │  └─ email.py            # Email 전송 채널
│  ├─ pyproject.toml         # API 런타임 의존성
│  └─ Dockerfile             # API 컨테이너 이미지 빌드
├─ mcp_server.py             # MCP 도구 래퍼 (notify_health/send_*)
├─ docker-compose.yml        # 단일 서비스 실행 정의
├─ .env.example              # 환경변수 템플릿
├─ README.md                 # 영문 문서
├─ README_ko.md              # 국문 문서
├─ AGENTS.md                 # 에이전트 연동 가이드
└─ llms.txt                  # LLM 친화 요약 문서
```

## 2) 런타임 아키텍처

1. 클라이언트(서비스/스크립트/에이전트)가 `/notify`, `/notify/email`, `/notify/telegram` 호출
2. `main.py`에서 요청 검증 후 채널 함수 호출
3. 채널 모듈:
   - Telegram: `channels/telegram.py` → Bot API 호출
   - Email: `channels/email.py` → SMTP(STARTTLS) 발송
4. `/health`는 텔레그램/이메일 활성 상태를 환경변수 기준으로 반환

## 3) Email 발신 라우팅 규칙

`source` 문자열 기반으로 `config.py`에서 발신 프로필을 자동 선택합니다.

- `ddok.ai` 포함 → ddok 프로필
- `baeum.ai.kr`, `baeum.io.kr`, `baeum.ai` 포함 → baeum 프로필
- 미일치 → 기본 baeum 프로필

프로필별로 다음 값을 분리 관리:

- SMTP 인증(`SMTP_USER_*`, `SMTP_PASSWORD_*`)
- 표시 발신자(`SMTP_FROM_*`, `SMTP_FROM_NAME_*`)

## 4) 운영 배포 경로(현재 기준)

- 로컬 소스: `/Users/baem1n/Dev/company/notify-api`
- 운영 소스(250): `/home/baeumai/services/notify-api`
- 운영 실행: Docker Compose (`notify-api` 컨테이너, `:9009`)

## 5) 운영 업데이트 절차

1. 로컬에서 코드/문서 수정 및 테스트
2. Git 커밋/푸시
3. 250 서버에 파일 반영
4. `docker compose up -d --build` 재기동
5. `GET /health`, `POST /notify/email`로 기능 확인

## 6) 메일 전달성 체크 포인트

- SPF/DKIM/DMARC DNS 설정 완료 여부
- 발신자 주소와 SMTP 인증 계정 정합성
- 주요 수신사(네이버/다음/지메일) 수신함·스팸함 동시 확인

