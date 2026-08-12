# 📘 n8n 설정 및 배포 가이드

## 🚀 빠른 시작

### 1단계: Docker에서 n8n 실행
```bash
docker run -it --rm --name n8n -p 5678:5678 \
  -e N8N_BASIC_AUTH_ACTIVE=true \
  -e N8N_BASIC_AUTH_USER=admin \
  -e N8N_BASIC_AUTH_PASSWORD=your_password \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n
```

**확인**: http://localhost:5678에 접속 → 관리자 계정으로 로그인

---

## 2️⃣ 자격증명 설정 (Credentials)

### Claude API 연결
1. **n8n 대시보드** → Credentials (왼쪽 메뉴)
2. **New** → HTTP Header Auth
3. 설정값:
   ```
   이름: claude-api-key
   
   Headers:
   - Key: Authorization
     Value: Bearer YOUR_ANTHROPIC_API_KEY
   
   - Key: anthropic-version
     Value: 2023-06-01
   ```
4. **Save** → 저장 완료

**API 키 발급**: [api.anthropic.com/account/api-keys](https://api.anthropic.com/account/api-keys)

### Notion API 연결
1. **n8n Credentials** → **New** → Notion API
2. 설정값:
   ```
   이름: notion-api
   Authentication: OAuth2
   ```
3. **Authorize** → Notion 계정으로 로그인
4. 앱 권한 승인

**자세한 설명**: [Notion 개발자 설정](https://developers.notion.com)

---

## 3️⃣ 워크플로우 Import & 설정

### Workflow JSON Import
1. **Workflows** → **Import from file**
2. `n8n_workflow_claude_notion.json` 선택
3. 노드 자동 로드됨

### 환경변수 설정
노드별로 다음 정보 입력:

#### Trigger (Cron) - 매일 실행
- **Interval**: 24시간 (또는 원하는 간격)
- **Time Zone**: Asia/Seoul

#### Notion Read 노드
- **Database ID**: Notion 페이지 URL에서 추출
  ```
  https://notion.so/3b5476045530813cbe93d91c10255157
                    ↑ 이 부분
  ```
- **Filter**: (선택) 특정 조건만 읽기
  예: Status = "Pending"

#### Claude API 노드
- **URL**: `https://api.anthropic.com/v1/messages`
- **Method**: POST
- **Body** (JSON):
  ```json
  {
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 1024,
    "messages": [
      {
        "role": "user",
        "content": "{{ $json.body }}"
      }
    ]
  }
  ```

#### Notion Write 노드
- **Database ID**: 위와 동일
- **Properties**:
  - Title: {{ $json.title }}
  - Content: {{ $json.content }}
  - Status: Completed

---

## 4️⃣ 에러 처리 및 로깅

### 재시도 설정 (Retry)
각 노드별로:
1. 노드 **Settings** (톱니바퀴 아이콘)
2. **Retry on fail** 활성화
3. Max Retries: 3
4. Wait Between Retries: 30초

### 오류 발생 시 알림
Slack 노드 추가:
```json
{
  "type": "n8n-nodes-base.httpRequest",
  "method": "POST",
  "url": "YOUR_SLACK_WEBHOOK_URL",
  "body": {
    "text": "❌ n8n 오류 발생!\n에러: {{ $json.error }}"
  }
}
```

**Slack Webhook 생성**: [api.slack.com/messaging/webhooks](https://api.slack.com/messaging/webhooks)

---

## 5️⃣ 워크플로우 실행 및 모니터링

### 수동 실행
- **Execute Workflow** 버튼 클릭
- 실시간 로그 확인

### 자동 실행 활성화
1. 워크플로우 **Settings** → **Activate**
2. Cron 트리거가 지정된 시간에 자동 실행

### 실행 로그 확인
- **Executions** 탭
- 각 실행 결과 상세 확인
- 입출력 데이터 확인 가능

---

## 🔍 주요 노드 설명

### Cron Trigger
- **역할**: 정해진 시간에 워크플로우 시작
- **설정**: 시간, 분, 요일, 월
- **예**: "매일 오전 9시" = `0 9 * * *`

### Notion Query
- **역할**: Notion 데이터베이스에서 데이터 읽기
- **출력**: 페이지 배열 (각각 title, properties)

### HTTP Request (Claude API)
- **역할**: Claude에 메시지 전송 및 응답 받기
- **응답**: JSON 형태 (`content[0].text`)

### Notion Create
- **역할**: Notion에 새 페이지 생성
- **필수**: Database ID + Properties

### Slack Webhook
- **역할**: Slack 채널에 메시지 발송
- **용도**: 완료 알림, 오류 알림

---

## 📊 데이터 흐름도

```
┌─────────────────┐
│  Daily Trigger  │ (24시간마다)
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│ Read Notion Data    │ 대기 중인 항목 읽기
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ Claude 분석/생성    │ 텍스트 분석 및 내용 생성
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ Write to Notion     │ 결과를 페이지에 저장
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ Slack 알림 발송     │ 완료 통지
└─────────────────────┘
```

---

## 🐛 문제 해결

### 문제: API 키 오류
**원인**: 잘못된 키 또는 형식 오류
**해결**:
1. API 키 다시 생성
2. "Bearer " 접두사 확인
3. 크레덴셜 재저장

### 문제: Notion 연결 실패
**원인**: 권한 부족
**해결**:
1. Integration 설정에서 Database 권한 확인
2. Database 공유 설정 재확인
3. 토큰 새로고침

### 문제: 데이터 형식 오류
**원인**: Notion 필드와 Claude 출력 형식 불일치
**해결**:
1. 노드에서 데이터 변환 추가 (Function 노드)
2. JSON 검증 (Set 노드)
3. 로그에서 실제 데이터 확인

---

## 📋 체크리스트

### 초기 설정
- [ ] Docker 설치 및 n8n 컨테이너 실행
- [ ] n8n 웹 UI 접속 확인
- [ ] Claude API 키 발급
- [ ] Notion Integration 생성

### 워크플로우 구성
- [ ] Claude Credentials 추가
- [ ] Notion Credentials 추가
- [ ] workflow.json Import
- [ ] Database ID 입력

### 테스트 및 배포
- [ ] 워크플로우 수동 실행 (Execute)
- [ ] 로그에서 성공 확인
- [ ] 자동 실행 활성화 (Activate)
- [ ] 첫 자동 실행 모니터링

### 모니터링
- [ ] Slack 알림 테스트
- [ ] 오류 처리 동작 확인
- [ ] 주기적 실행 로그 확인

---

## 🔗 참고 자료

- **n8n 공식**: https://docs.n8n.io
- **Claude API**: https://docs.anthropic.com
- **Notion API**: https://developers.notion.com
- **n8n 커뮤니티**: https://community.n8n.io

---

**최종 수정**: 2026-08-12  
**작성자**: Claude  
**상태**: ✅ 배포 준비 완료
