# Notify API

[English](README.md) | [한국어](README_ko.md)

경량 셀프호스팅 알림 게이트웨이. 하나의 REST API로 Telegram과 Email 알림을 발송합니다.

개발자, DevOps 팀, 그리고 **AI Agent**가 어떤 서비스에서든 간편하게 알림을 보낼 수 있도록 설계되었습니다.

## 주요 기능

- **Telegram** 알림 (Bot API)
- **Email** 알림 (SMTP / Gmail)
- **Source 기반 발신자 라우팅** (`ddok.ai` vs `baeum.ai*`)
- **통합 엔드포인트** — 하나의 API로 여러 채널 발송
- **심각도 레벨** — info, warning, critical (이모지 표시)
- **출처 태깅** — 어떤 서비스가 알림을 보냈는지 식별
- **Docker 배포** — `docker compose up` 한 줄로 실행
- **AI Agent 친화** — 구조화된 API, `AGENTS.md`로 LLM 즉시 연동

## 빠른 시작

### 1. 클론 & 설정

```bash
git clone https://github.com/BAEM1N/notify-api.git
cd notify-api
cp .env.example .env
```

`.env` 파일에 크레덴셜 입력:

```env
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
```

### 2. 배포

```bash
docker compose up -d
```

### 3. 테스트

```bash
curl http://localhost:9009/health
```

## API 레퍼런스

### 헬스체크

```
GET /health
```

```json
{
  "status": "ok",
  "channels": { "telegram": true, "email": false }
}
```

### 알림 발송 (통합)

```
POST /notify
Content-Type: application/json
```

```json
{
  "channel": "telegram",
  "title": "배포 완료",
  "message": "v2.1.0 프로덕션 배포가 완료되었습니다",
  "level": "info",
  "source": "ci-pipeline"
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `channel` | `telegram` \| `email` \| `all` | 아니오 (기본: `telegram`) | 발송 채널 |
| `title` | string | 예 | 알림 제목 (최대 200자) |
| `message` | string | 예 | 알림 본문 (최대 4000자) |
| `level` | `info` \| `warning` \| `critical` | 아니오 (기본: `info`) | 심각도 |
| `source` | string | 아니오 | 발송 서비스 식별자 |

### Telegram 전용 발송

```
POST /notify/telegram
Content-Type: application/json
```

```json
{
  "title": "경고",
  "message": "CPU 사용률이 90%를 초과했습니다",
  "level": "critical",
  "source": "monitoring"
}
```

### Email 전용 발송

```
POST /notify/email
Content-Type: application/json
```

```json
{
  "title": "주간 리포트",
  "message": "시스템 가동률: 99.97%",
  "level": "info",
  "source": "https://qna.ddok.ai",
  "to": "team@example.com"
}
```

하위 호환을 위해 `title` 대신 `subject` 필드도 허용합니다.

### 응답 형식

모든 엔드포인트 공통:

```json
{
  "ok": true,
  "channels": { "telegram": true },
  "errors": {}
}
```

## Telegram Bot 설정

1. Telegram에서 [@BotFather](https://t.me/BotFather)에게 메시지
2. `/newbot` 입력 후 안내에 따라 봇 생성
3. **Bot Token** 복사
4. 봇에게 아무 메시지를 보낸 뒤 **Chat ID** 확인:
   ```bash
   curl https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
5. `.env`에 두 값을 입력

## Email 설정 (선택)

Gmail / Google Workspace SMTP 사용 시:

1. [2단계 인증](https://myaccount.google.com/security) 활성화
2. [앱 비밀번호](https://myaccount.google.com/apppasswords) 생성
3. SMTP 기본 설정을 `.env`에 추가:
   ```env
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-default-email@gmail.com
   SMTP_PASSWORD=your-app-password
   ```
4. (선택) 브랜드/도메인별 발신자 라우팅 설정:
   ```env
   SMTP_FROM_BAEUM=no-reply@baeum.ai.kr
   SMTP_FROM_NAME_BAEUM=배움 에이아이
   SMTP_USER_BAEUM=no-reply@ddok.ai
   SMTP_PASSWORD_BAEUM=your-app-password

   SMTP_FROM_DDOK=no-reply@ddok.ai
   SMTP_FROM_NAME_DDOK=주식회사 똑똑한청년들
   SMTP_USER_DDOK=no-reply@ddok.ai
   SMTP_PASSWORD_DDOK=your-app-password

   SMTP_URL_KEYWORDS_BAEUM=baeum.ai.kr,baeum.io.kr,baeum.ai
   SMTP_URL_KEYWORDS_DDOK=ddok.ai
   ```

라우팅 우선순위:
- `source`에 `ddok.ai` 포함 → ddok 발신자 프로필
- `source`에 `baeum.ai.kr`, `baeum.io.kr`, `baeum.ai` 포함 → baeum 발신자 프로필
- 그 외 → 기본값으로 baeum 발신자 프로필

## Grafana 연동

Notify API는 Grafana의 내장 Telegram 알림과 병행 사용 가능합니다:

```
Grafana Alert Rules → Telegram Contact Point → Telegram
기타 서비스들      → Notify API (:9009)      → Telegram / Email
```

Grafana에서 Telegram Contact Point 추가 (API):

```bash
curl -X POST http://your-grafana:3000/api/v1/provisioning/contact-points \
  -H "Authorization: Basic <base64>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Telegram",
    "type": "telegram",
    "settings": {
      "bottoken": "your-bot-token",
      "chatid": "your-chat-id"
    }
  }'
```

## MCP Server (AI Agent 연동)

Notify API에는 [MCP](https://modelcontextprotocol.io/) 서버가 내장되어 있어, AI Agent(Claude Code 등)가 REST 호출 없이 MCP 프로토콜로 직접 알림을 보낼 수 있습니다.

### 설정

```bash
# 의존성 설치 (최초 1회)
cd notify-api
uv sync

# Claude Code에 등록 (사용자 범위)
claude mcp add --transport stdio --scope user notify_mcp \
  -e NOTIFY_API_URL=http://localhost:9009 \
  -- uv run --directory /path/to/notify-api mcp_server.py
```

### MCP 도구 목록

| 도구 | 설명 |
|------|------|
| `notify_health` | API 상태 및 채널 가용성 확인 |
| `notify_send_telegram` | Telegram 알림 발송 |
| `notify_send_email` | Email 알림 발송 |
| `notify_send` | 통합 발송 (채널 지정 가능) |

### Claude Code 슬래시 커맨드

스킬 파일을 설치하면 `/notify`로 즉시 사용 가능합니다:

```
/notify 배포 완료
/notify --critical 서버 다운! 즉시 확인 필요
/notify --email Weekly Report: System uptime 99.97%
/notify --all 점검 공지: 오늘 22시 서버 점검
/notify --health
```

## 사용 예시

### Shell 스크립트에서

```bash
notify() {
  curl -s -X POST http://localhost:9009/notify/telegram \
    -H "Content-Type: application/json" \
    -d "{\"title\":\"$1\",\"message\":\"$2\",\"level\":\"${3:-info}\",\"source\":\"${4:-shell}\"}"
}

notify "백업 완료" "데이터베이스 백업이 완료되었습니다" "info" "cron"
```

### Python에서

```python
import httpx

def notify(title: str, message: str, level: str = "info", source: str = ""):
    httpx.post("http://localhost:9009/notify/telegram", json={
        "title": title,
        "message": message,
        "level": level,
        "source": source,
    })

notify("학습 완료", "모델 정확도: 94.2%", "info", "ml-pipeline")
```

### AI Agent에서

[AGENTS.md](AGENTS.md)에서 구조화된 연동 가이드를 확인하세요.

## 환경 변수

| 환경 변수 | 필수 | 기본값 | 설명 |
|----------|------|--------|------|
| `TELEGRAM_BOT_TOKEN` | 예 | — | Telegram Bot API 토큰 |
| `TELEGRAM_CHAT_ID` | 예 | — | Telegram 채팅/그룹 ID |
| `SMTP_HOST` | 아니오 | `smtp.gmail.com` | SMTP 서버 호스트 |
| `SMTP_PORT` | 아니오 | `587` | SMTP 서버 포트 |
| `SMTP_USER` | 아니오 | — | 공통 fallback SMTP 사용자 |
| `SMTP_PASSWORD` | 아니오 | — | 공통 fallback SMTP 비밀번호 |
| `SMTP_FROM_BAEUM` | 아니오 | `no-reply@baeum.ai.kr` | baeum 발신자 이메일 주소 |
| `SMTP_FROM_NAME_BAEUM` | 아니오 | `배움 에이아이` | baeum 발신자 표시 이름 |
| `SMTP_USER_BAEUM` | 아니오 | — | baeum 발신자 SMTP 사용자 |
| `SMTP_PASSWORD_BAEUM` | 아니오 | — | baeum 발신자 SMTP 비밀번호 |
| `SMTP_FROM_DDOK` | 아니오 | `no-reply@ddok.ai` | ddok 발신자 이메일 주소 |
| `SMTP_FROM_NAME_DDOK` | 아니오 | `주식회사 똑똑한청년들` | ddok 발신자 표시 이름 |
| `SMTP_USER_DDOK` | 아니오 | — | ddok 발신자 SMTP 사용자 |
| `SMTP_PASSWORD_DDOK` | 아니오 | — | ddok 발신자 SMTP 비밀번호 |
| `SMTP_URL_KEYWORDS_BAEUM` | 아니오 | `baeum.ai.kr,baeum.io.kr,baeum.ai` | baeum 라우팅 키워드(콤마 구분) |
| `SMTP_URL_KEYWORDS_DDOK` | 아니오 | `ddok.ai` | ddok 라우팅 키워드(콤마 구분) |
| `GMAIL_CREDENTIALS_PATH` | 아니오 | `/app/credentials/credentials.json` | Gmail API 인증 파일 경로 |

## 기술 스택

- **FastAPI** + **Uvicorn** — 비동기 HTTP 서버
- **httpx** — 비동기 Telegram API 클라이언트
- **aiosmtplib** — 비동기 SMTP 클라이언트
- **pydantic-settings** — 환경 변수 기반 설정
- **Docker** — 컨테이너 배포
- **FastMCP** — AI Agent 연동을 위한 MCP 서버

## 라이선스

[MIT](LICENSE)
