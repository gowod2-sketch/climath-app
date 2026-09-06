# 주간지 × mathuit — 통합 인수인계 (단일본)

이 문서가 **유일한 최신본**이다. 아래 두 개는 이 문서로 대체되며 더 갱신하지
않는다 (참고용으로만 남겨둠, 삭제는 안 함):
- `climath-app` 브랜치 `claude/work-preparation-xpb5nj` →
  `docs/주간지_mathuit_통합_인수인계.md` ("H.주간지 분류" 세션 작성)
- `shuttle.plan`/`climath-app` 브랜치 `claude/climath-daily-dashboard-0vir67` →
  `Mathuit_주간지_통합인수인계.md` ("CLIMATH 데일리운영 대시보드" 세션 작성)

두 세션이 서로 모른 채 "주간지 문항을 어떻게 다룰까"에 각자 다른 설계를
내놓았다 — 하나는 mathuit 앱으로 흡수, 하나는 계속 LaTeX 인쇄물로 두고
QR로 오답만 수집. **둘 다 필요하다고 확정** (2026-09-06, 사용자 결정) —
경쟁안이 아니라 **서로 다른 용도의 병행 트랙**이다. 이 문서는 그 둘을
한 자리에 모으고, 데이터 소스가 갈라지지 않게 조율 규칙을 못박는다.

작성 시점: 2026-09-06. 관련 저장소: `gowod2-sketch/climath-app`(public,
앱 코드), `gowod2-sketch/shuttle.plan`(private, 주간지 분류·데이터).

---

## 0. 두 트랙 요약

| | 트랙 1 — mathuit 흡수 | 트랙 2 — QR 오답체크 |
|---|---|---|
| 목적 | 주간지 문항을 mathuit 앱 안 퀴즈 페이지로 상시 노출 | 인쇄된 주간지의 오답을 스캔으로 수집 → 개인 오답노트 재조판 |
| 주간지 원본 형태 | 계속 LaTeX/PDF로 인쇄 (바뀌지 않음) | 계속 LaTeX/PDF로 인쇄 (바뀌지 않음) |
| 이 기능이 다루는 산출물 | mathuit 웹앱 페이지 (신규) | 개인화 LaTeX→PDF 오답노트 (신규) |
| 데이터 출처 | `shuttle.plan`의 `round0N/조판/묶음.json` | `weekly.tex` 원본(학생용, 정답 없는 버전) |
| 상태 | 샘플 문항 1개 릴리즈됨(커밋 `18fb8ea`), 나머지는 설계만 확정 | 코드 4개 작성 완료, 미검증 다수 |
| 작업 저장소 | `climath-app` (앱 코드) | `climath-app`/`shuttle.plan` (신규 정적 페이지 + 스크립트) |

**중요**: 두 트랙 다 "주간지는 계속 인쇄물"이 전제다. mathuit 통합은
주간지를 대체하는 게 아니라 **같은 문항을 상시 열람 가능한 두 번째
채널로 여는 것**, QR 오답체크는 **인쇄물 사용을 전제로 한 사후 피드백
수집**이다. 서로 경쟁하지 않는다 — 다만 둘 다 "문항 하나의 정규 표현"이
필요하므로 아래 4절의 조율 규칙을 반드시 지킬 것.

---

## 1. 트랙 1 — 주간지를 mathuit 앱에 통합

*(원문: "H.주간지 분류" 세션, `climath-app` 브랜치 `claude/work-preparation-xpb5nj`)*

**분류(문항 뽑기·유형 나누기·100제 선정·검산·해설 쓰기)는 climath-app
저장소 몫이 아니다.** 그건 `shuttle.plan` 저장소(브랜치
`claude/work-preparation-xpb5nj`)가 계속 맡는다. climath-app에서는
**mathuit에 주간지를 얹는 기능 개발만** 한다.

### 확정된 것
| | |
|---|---|
| 통합 여부 | **한다.** mathuit을 "교재 여러 개를 담는 플랫폼"으로 보고, 새 교재로 "주간지"를 추가 |
| 콘텐츠 단위 | **한 페이지 = 한 문항.** mathuit 기존 방식(`pages[]` 하나=화면 하나) 그대로. "펼침면 하나에 문항 여러 개"로 보여주는 프로토타입([에스킬라 리더](https://claude.ai/code/artifact/332d6cbb-3c5a-41a5-a511-5296e07f2de2), mathuit과 무관한 별도 아티팩트)은 **버린다** — 단, 확대 팝업에서 "해설 보기" 누르면 정답 표시+해설 펼쳐지는 상호작용은 참고할 만함 |
| 로그인 | 공유 비밀번호 2개(교사용/학생용). 계정별 로그인(Netlify Identity·Supabase Auth) 안 씀 — 서버·DB 없이 정적 사이트 유지가 목적 |
| 목차 | mathuit에 **이미 있음** — `pages[]`를 회차 단위로 채우면 `buildTOC()`가 자동으로 구역(회차)별로 갈라줌 |
| 교사/학생 화면 차이 | **다르다, 확정.** 로그인 아이디(공유 비밀번호 2개)에 따라 분기 — 교사용 계정에서는 문항 페이지에 해설(`sol`)이 노출되고, 학생용 계정에서는 숨김 |
| 즐겨찾기(책갈피) | **신규 기능으로 확정.** 문항 페이지마다 책갈피 버튼. 역할에 따라 필터 모드 이름·용도가 다름 — 학생: **복습 모드**, 교사: **수업 모드**. 아래 "즐겨찾기/필터 모드" 절 참고 |

### 즐겨찾기(책갈피) → 역할별 필터 모드 (2026-09-06 결정, 같은 날 세부화)

학생·교사 둘 다 문항 페이지에서 책갈피 버튼으로 특정 문항을 표시해두고,
표시된 문항만 걸러서 몰아보는 모드로 전환할 수 있어야 한다. **단, 이
필터 모드는 역할에 따라 이름과 용도가 다르다:**

- **학생 → "복습 모드"**: 자신이 즐겨찾기한(또는 틀렸던) 문항만 걸러서
  개인 복습용으로 다시 품
- **교사(나) → "수업 모드"**: 내가 즐겨찾기한 문항만 몰아서, 수업 중
  칠판 설명용으로 순서대로 넘겨봄 — 학생 개개인의 오답과 무관하게
  **교사 자신의 즐겨찾기 목록**을 기준으로 필터링

즉 필터링 로직(즐겨찾기된 것만 추출) 자체는 같지만, **즐겨찾기 목록이
역할별로 분리된 별도 데이터**다 — 교사 계정으로 찍은 책갈피와 학생
계정으로 찍은 책갈피가 서로 섞이면 안 됨. §1 "교사/학생 화면 차이"에서
쓰기로 한 role 플래그(로그인 계정 구분)를 즐겨찾기 저장 키에도 그대로
써서 네임스페이스를 나눌 것(예: `localStorage` 키를 `bookmark_teacher_*` /
`bookmark_student_*`로 분리, 또는 Supabase를 쓸 경우 `role` 컬럼 추가).

- **저장 위치**: mathuit은 서버가 없는 정적 사이트이므로 1차로는
  `localStorage`(기기별)에 저장 — 계정 개념이 공유 비밀번호뿐이라 사용자별
  서버 동기화는 지금 인프라로는 못 함. 기기를 바꾸면 안 남는다는 제약을
  감수할지, 아니면 Supabase에 (2절 트랙 2가 이미 쓰는) 익명 키 하나로
  저장할지는 새 세션이 정할 것 — 후자를 택하면 트랙 2의 `weekly_wrong_answers`
  와 같은 "anon INSERT만, SELECT 없음" 원칙을 그대로 따를 것(C9 반복 금지).
  단, 교사의 수업 모드는 교사 본인이 다시 조회(SELECT)할 수 있어야 하므로
  트랙 2와 똑같이 "INSERT만" 허용하면 안 됨 — 이 부분은 트랙 2 원칙을
  그대로 복사하지 말고 별도로 설계할 것.
- **필터 기준(학생 쪽)**: 학생의 즐겨찾기와 "오답 표시"(트랙 2 QR
  오답체크로 쌓인 Supabase 데이터)가 같은 개념인지 별개인지 정할 것.
  지금 둘은 서로 다른 시스템이라 자동으로 안 이어진다 — 이어붙이면
  "QR로 체크한 오답이 mathuit 복습 모드에도 자동으로 뜨는" 기능이 되는데,
  이건 3절 조율 규칙의 "세 번째 방법"에 해당하므로 만들기 전에 이 문서를
  먼저 갱신할 것.
- **UI**: `buildTOC()`가 이미 `pages[]`를 필터링해 보여주는 구조이므로,
  두 모드 다 같은 컴포넌트에 "즐겨찾기만" 필터를 얹는 것으로 구현 가능해
  보임 — 새 UI를 새로 만들기보다 TOC 필터링 로직 재사용을 먼저 검토하고,
  그 위에 역할별 즐겨찾기 목록만 갈아 끼우는 구조로 갈 것.

### mathuit 실측 사실
`mathuit/`은 "수열의 극한" 개념 하나를 설명하는 단일 흐름 PWA (정적 사이트,
`build.py`가 `content/*.md` → `index.html`의 `/*DATA:BEGIN*/.../*DATA:END*/`
블록에 JSON 주입, Netlify가 push마다 자동 빌드·배포). 라이브:
mathuit-textbook.netlify.app / 편집기: mathuit-editor.netlify.app.

- **필기 — 된다.** `<canvas class="inkc">`로 실제로 그림. 800~1090번째 줄
  근처 `penOn` 로직. 길게 누르면 진입, 두 손가락으로 나가기.
- **목차 — 이미 있다.** `.tocpanel` 슬라이드업, `buildTOC()`가 `pages[]`를
  `sec`별로 묶음. 항목 클릭 시 `data-go`로 점프, `markTOC()`가 현재 위치 표시.
- **퀴즈(문항) 자리 — 2026-09-06 정정: 실제로는 이미 완성돼 있었다.**
  이전 판(트랙 1 원문)이 "`var quiz='';`만 있고 미완성"이라고 적었던 건
  **틀렸다** — 실측 없이 코드를 겉핥기로 읽은 결과였다. 실제로 확인하니:
  - `build.py`의 `parse_concept()`이 프런트매터 `kind: quiz`를 받으면
    `question`·`problemEq`·`options`(1~5)·`answer`를 페이지 데이터에 담음
  - `editor.html`에 편집 UI 이미 있음 (문제 모드 토글, 보기 5개 입력, 정답 지정)
  - **`index.html`의 `renderPageHTML()`에 `if(p.kind==='quiz'){...return ...}`
    분기가 이미 있고, 문제·보기 5개를 실제로 그린다.** 사람 개발자가
    2026-08-13 커밋 `26a4e1d`("add interactive sample quiz")에서 만든 것 —
    `2f99d5c`(같은 날, 5시간 뒤)가 아니라 이 커밋이 진짜 quiz 렌더링 원본.
    그 뒤에 나오는 `var quiz='';`는 quiz가 아닌 페이지용 코드로,
    quiz 분기가 먼저 `return`하기 때문에 quiz 페이지에서는 아예 실행 안
    되는 죽은 코드다 — "빈 문자열"이 아니라 "도달 못 하는 분기"였다.
  - CSS·상호작용도 있음 — `.quizopt`(보기 클릭), `selectQuizOption()`(클릭 시
    체크 표시+사운드)
  - **2026-09-06 샘플 릴리즈로 실제 확장함** (커밋 `18fb8ea`,
    `claude/mathuit-session-handoff-im93kp` 브랜치): `build.py`에 `sol`
    (해설)·`src`(출처) 필드 추가, `index.html`에 MathJax 로드(문항 페이지
    전용, raw LaTeX `$...$` 렌더) + 정답/오답 색 표시 + "해설 보기" 토글을
    얹고, shuttle.plan `round03/조판/묶음.json`의 실제 문항 1개
    (`content/concept/w3-01.md`)를 넣어 화면까지 확인함(정답/오답 클릭·
    해설 토글은 헤드리스로 직접 검증, MathJax 자체 렌더링은 그 세션 샌드박스가
    cdnjs 아웃바운드를 막아 로컬 미검증 — Netlify 실배포에서 최초 확인 필요).
    **모의고사 배지(`모의`/`모의꼴`) 필드는 아직 안 뚫음** — 필요해지면 이번
    `sol`/`src` 추가한 자리에 같이 얹을 것.
  - 남은 것: 교사/학생 해설 노출 분기(§ "확정된 것" 표, 로그인 role별 표시
    여부), 즐겨찾기/필터 모드, `editor.html`에 `sol`/`src` 편집 UI 추가,
    목차 2단 구조 — 전부 미착수
- **인증 — 없다.** `netlify/functions/save-content.js`(편집기 저장을 GitHub
  커밋으로 바꿔줌, `GITHUB_TOKEN` 사용)만 있고 로그인·세션·비밀번호 검사 코드는
  전혀 없음. 공유 비밀번호면 클라이언트 쪽(sessionStorage 플래그)으로 붙일
  수 있지만, 비밀번호 자체를 어디에 어떻게 저장할지(소스에 해시만 심을지,
  Netlify 환경변수+서버리스 함수로 서버에서만 검증할지)는 미정 — 새 세션이 정할 것

### 디자인 규칙 (`mathuit/README.md`, 바꾸지 말 것)
라이트 모드 고정, 인디고 `#4C5FD5`·바이올렛 `#7B5CE6`·코랄 `#F2653E`·잉크
`#1B2033`, 수식은 배경 박스 없이 검정 볼드 세리프, 페이지 전환 슬라이드
340ms(롤링·페이지컬 금지). 주간지 문항 페이지도 이 규칙 안에서 가는 게
자연스러움 — 조판/수업판이 쓰는 네이비 `#203F70`·레드 `#D10B35` 배색과는
다른 계열이니 두 색 체계 조율 필요.

### shuttle.plan 쪽 데이터 (통합에 쓸 원본)
- 저장소: `gowod2-sketch/shuttle.plan`, 브랜치 `claude/work-preparation-xpb5nj`
- 회차 데이터: `round0N/조판/묶음.json` (N=3 조판 준비 끝, 4·5는 분류·검산
  끝 최근 완성, 1·2는 예전 방식으로 이미 발행돼 스키마가 다를 수 있음 —
  새로 확인 필요)
- 문항 필드(3회차 기준): `no`(번호)·`t`(유형 코드)·`body`(발문, `$...$` 안
  raw LaTeX)·`ch`(보기 5개, raw LaTeX)·`ans`("1"~"5")·`sol`(해설, `\n` 단계
  구분, raw LaTeX)·`d`(난도 점수)·`src`(출처, 예: "휘문고 2026 10번")·
  `모의`/`모의꼴`(기출/기출변형 배지)·`del`(뺀 문항 표시)
- 최상위: `TYPES`(유형 코드→설명), `ORDER`(유형 순서), `LAYOUT`(편집기 지면
  배치 — 한 페이지 한 문항 모델에서는 안 써도 됨, `ORDER`+유형 안 난도순만
  정하면 됨), `mission`(표지 문구)
- **수식 렌더러가 다르다** — mathuit 자체 `mathify()`/`prose()`(`a_n` 같은
  낱말 직접 파싱해 이탤릭 처리) vs shuttle.plan(MathJax가 `$...$` 그대로
  그림). **통일 필요.** 문항 본문을 mathuit `mathify()`가 소화 못 할
  가능성 높음(복소수 켤레 `\overline{}`, 분수 `\frac{}{}` 등이 mathuit
  `SYM` 표에 없음). 가장 안전한 길: **문항 페이지에서만 MathJax 사용**,
  mathuit 라이트모드·세리프 볼드 규칙에 맞게 MathJax 폰트만 맞춤
- 참고용 생성기: `pipeline/리더_데이터.py` (묶음.json → 펼침면 단위 JSON,
  문항 렌더링은 `수업판_만들기.py`의 `문항들()` 재사용) — 펼침면 모델이라
  그대로는 못 쓰지만 `stem_html`의 조건·보기 상자 가르기 로직은 참고할 만함

### 아직 안 정한 것
1. 비밀번호 검증 위치 (완전 클라이언트 vs 서버리스 함수)
2. ~~교사/학생 화면 차이~~ → **확정됨**: 교사 계정은 해설 노출, 학생 계정은
   숨김 (위 "확정된 것" 표 참고). 단 **구현 방법은 미정** — 로그인 성공
   시 `sessionStorage`에 role 플래그를 심고, 이미 렌더링되는 `sol` 블록을
   그 플래그로 감싸 학생 계정에서 숨기면 될 듯(§ mathuit 실측 사실의
   2026-09-06 정정 참고 — quiz 렌더링과 `sol` 표시는 이미 있음)
3. 수식 렌더러 통일 방식 — **샘플로 일부 검증됨**: 문항 페이지 전용으로
   MathJax를 얹는 방식이 코드상 동작함(§ mathuit 실측 사실 참고). 다만
   MathJax의 실제 LaTeX 렌더링 자체는 샌드박스에서 cdnjs 아웃바운드가
   막혀 있어 로컬 미검증 — 실배포에서 최초 확인 필요
4. ~~`quiz` 렌더링 완성~~ → **완성돼 있었다(정정) + 샘플로 sol/src까지
   확장함** — 이제 남은 건 교사/학생 분기 렌더링(항목 2)과 즐겨찾기
   버튼(위 "즐겨찾기(책갈피) → 역할별 필터 모드" 절)뿐
5. 회차가 여럿일 때 목차 2단 구조 (지금 TOC는 구역별 평면 목록 하나뿐 —
   "주간지 → 회차 선택 → 문항 목록" 구조가 필요하면 `buildTOC()` 확장)
6. 즐겨찾기 저장 위치(localStorage vs Supabase)와 "즐겨찾기 = 오답 표시"
   여부를 같이 볼지 별개로 둘지 (위 "즐겨찾기(책갈피) → 복습 모드" 절 참고)

### 하지 말 것
- mathuit은 **라이브 서비스**(mathuit-textbook.netlify.app). 기존 "수열의
  극한" 콘텐츠(개념·팁·필기)를 건드리거나 깨뜨리지 말 것 — `content/concept/`·
  `content/tip/`은 그대로 두고 주간지는 새 콘텐츠 종류로 옆에 추가
- `index.html`의 `/*DATA:BEGIN*/.../*DATA:END*/` 블록은 `build.py`가
  덮어쓰는 자리 — 손으로 고치지 말 것
- `sw.js` 내용을 고치면 캐시명 `mathtip-vN`을 반드시 올릴 것 — 안 그러면
  배포해도 사용자 화면이 안 바뀜

---

## 2. 트랙 2 — 주간지 QR 오답체크 → 개인 맞춤 오답노트

*(원문: "CLIMATH 데일리운영 대시보드" 세션, 브랜치
`claude/climath-daily-dashboard-0vir67`)*

### 목표
주간지 표지에 QR을 붙여 학생이 스캔 → 틀린 문항 번호 체크 → 서버에 쌓임
→ 여러 회차 데이터를 모아 학생별 오답노트를 자동으로 **LaTeX 재조판**.
(트랙 1과 달리 결과물이 mathuit 페이지가 아니라 **인쇄용 PDF**임에 주의.)

### 주간지 LaTeX 조판 구조 (이번에 실측한 핵심 사실)
Google Drive `climath-weekly` 폴더에서 관리, mathuit과는 완전히 별개 시스템.
```
xelatex weekly.tex   (×2 — 목차/참조 갱신을 위해 두 번)
```
설정: `climath-tokens.tex`(회차별 값 — 제목·연도·문항유형 구간),
`climath-style.sty`(레이아웃 매크로). `\TKenv`로 linux/mac/overleaf 스위치,
`\THEME`로 A(스탠다드)/B(에디토리얼) 두 양식.

각 문항은 개별 매크로 호출로 존재:
```latex
\prob{01}{...문항 본문...}
\probrep{02}{...문항 본문...}   % 반복유형 배지 붙는 버전
```
`01`이 **학생이 실제로 보는 인쇄 번호**. 문항 유형은 `\TKtypelist`에서
번호 구간으로 묶여 인덱스 탭에 표시됨. **문항이 번호로 개별 주소 지정
가능하다는 사실이 오답체크 기능 전체의 전제.**

산출물: 회차별로 강사용/학생용 PDF, 빠른정답, 전수검수보고서, 배치표가
따로 있음. **오답노트는 반드시 정답·해설 없는 학생용 원본
(`weekly.tex` 소스)에서 문항을 뽑아야 함** — 강사용/정답지에서 뽑으면
정답이 노출됨.

### 설계 결정
- **QR은 회차당 1개(공용)**, 학생별 개인화 QR 아님 — LaTeX 배치 시스템이
  이미 무거워 학생별 PDF 배치 생성을 새로 얹는 비용이 이 기능 하나 치고
  너무 큼. 학생 식별은 웹페이지에서 이름 선택(동명이인 있어 학교·학년 병기)
- **QR 이미지 파일을 따로 관리 안 함.** LaTeX `qrcode` 패키지로 URL에서
  직접 그림 (⚠️ 컴파일 자체 미검증 — 조판 세션에서 1회 확인 필요)
- **오답 데이터 테이블에 anon SELECT를 안 줌.** 기존 `students`/`attendance`
  테이블은 RLS가 꺼져 있어 anon 키만으로 전건 읽기·삭제가 되는 문제(C9,
  미해결, 4절 참고)가 있는데, 새 테이블은 처음부터 INSERT만 허용해 같은
  실수를 반복하지 않게 설계

### 만든 파일 (`SendUserFile`로 전달됨, 저장소엔 아직 미커밋)

**`SCHEMA.sql`** (미실행 제안, Supabase에서 직접 실행할 것)
```sql
create table public.weekly_issues (
  round_id       text primary key,
  title          text not null,
  total_problems int  not null,
  created_at     timestamptz not null default now()
);
alter table public.weekly_issues enable row level security;
create policy weekly_issues_anon_select
  on public.weekly_issues for select to anon using (true);

create table public.weekly_wrong_answers (
  id             bigint generated always as identity primary key,
  round_id       text not null references public.weekly_issues(round_id),
  student_name   text not null,
  student_school text,
  student_grade  text,
  wrong_numbers  int[] not null default '{}',
  submitted_at   timestamptz not null default now()
);
alter table public.weekly_wrong_answers enable row level security;
create policy weekly_wrong_anon_insert
  on public.weekly_wrong_answers for insert to anon with check (true);
-- select/update/delete 정책은 의도적으로 없음
```
집계(대시보드용, 최신 제출만 인정):
```sql
with latest as (
  select distinct on (round_id, student_name) *
  from weekly_wrong_answers
  order by round_id, student_name, submitted_at desc
)
select round_id, unnest(wrong_numbers) as problem_no, count(*) as miss_count
from latest group by round_id, problem_no order by round_id, miss_count desc;
```

**`index.html`** — 학생이 QR 찍고 들어가는 페이지. Supabase JS(jsdelivr
CDN) + 위 스키마 그대로 사용. 흐름: `?round=` 읽기 → `weekly_issues` 조회
(제목·문항수) → 학생 검색·선택 → 문항 번호 그리드에서 틀린 것 탭 → 제출.
climath-daily/climath-student와 같은 스택(정적 HTML, CSP 문제 없음 —
아티팩트 아니라 일반 사이트). 헤드리스 브라우저+mock Supabase로 전체
흐름(검색 필터, 동명이인 구분, 그리드 크기, 제출 payload) 검증함 — 예외 0건.
**실제 Supabase 연결은 미검증.**

**`extract_wrong_problems.py`** — 여러 회차 `weekly.tex`에서 지정한 문항
번호만 뽑아 하나의 tex로 합치는 스크립트. `\prob{NN}{...}`을 중괄호 깊이
매칭으로 찾음(정규식만으로는 중첩된 수식 중괄호 때문에 블록 끝을 못 잡음).
```bash
python3 extract_wrong_problems.py --out 학생명_오답노트.tex \
  --style climath-style --tokens climath-tokens.tex \
  1회차/weekly.tex:3,7,15  2회차/weekly.tex:1,9,22
```
합성 데이터(중첩 중괄호·이스케이프 포함)로 파서 로직 검증함. **실제
weekly.tex로는 아직 안 돌려봤다** — 처음 쓸 때 결과 tex를 열어 문항이
맞게 뽑혔는지 직접 확인할 것.

### 아직 안 된 것
1. `SCHEMA.sql`을 Supabase에서 실제로 실행 (원장이 직접)
2. LaTeX `qrcode` 패키지 컴파일 확인 + 실제 표지에 삽입 위치 조정
3. `extract_wrong_problems.py`를 실제 `weekly.tex` 1개에 시험 실행
4. `index.html`을 climath-student.netlify.app에 `wrong-check.html`로
   추가 배포 후 실제 Supabase 연결 테스트
5. Mathuit 데일리운영 대시보드에 "문항별 오답률" 패널 추가 (테이블이
   아직 없어서 미착수)

### 이번에 함께 고친 mathuit 빌드 버그 2건 (이 트랙과 무관, 별개 작업)
1. **팁 링크가 조용히 죽는 버그**: `prose()`가 링크 파싱보다 먼저 기호
   치환을 돌려서 팁 id에 `sum`·`oo` 같은 약어가 부분 문자열로 들어있으면
   (예: `sumval` → `&#8721;val`) 링크 정규식이 안 걸려 `<span>` 미생성.
   빌드는 통과하고 화면만 깨짐 → id를 자리표시자로 먼저 빼고 기호 치환 후
   복원하는 방식으로 수정.
2. **엔티티가 글자 그대로 노출되는 버그**: `mathify()`가 `&#8721;` 같은
   엔티티를 문자 단위로 쪼개 각각 별도 span에 가둬 `&`,`#`,`8`...가 개별
   렌더링됨 → 엔티티를 한 토큰으로 통과시키게 수정.
3. **`render_check()` 게이트 신설**: 위 두 유형은 기존 검증(생성된 `data-t`
   만 대조)이 애초에 잡지 못하는 구조였음 → 빌드 단계에서 직접 스캔해 막음.
- 검증: 수정 전후 전수 스캔 — 죽은 링크 2→0, 엔티티 파손 9→0, 바뀐 필드
  정확히 11개(=부수 변경 없음 확인).
- `content/_README.md`의 curve 카탈로그도 "위/아래 수렴" 행 이름이 뒤바뀐
  걸 실제 대입 검산 후 정정함.
- 하네스 교훈(`docs/harness/LESSONS.md`, 9회차 20개 항목) 핵심: 참조표는
  에이전트가 검증 없이 믿으므로 반드시 실행 검산한 값으로 채울 것 / 형식
  검증(빌드 통과)과 내용 검증(수학적으로 맞는가)을 분리할 것 / 재사용
  뼈대는 `docs/harness/TEMPLATE/`에 있음.

---

## 3. 두 트랙이 갈라지지 않게 — 조율 규칙

1. **문항 정규 표현은 shuttle.plan이 원본이다.** 트랙 1(묶음.json)과
   트랙 2(weekly.tex 매크로)가 같은 회차의 같은 문항을 서로 다른 필드명·
   형식으로 다루더라도, **둘 다 shuttle.plan의 분류·검산 결과에서 파생된
   것이어야 한다** — 어느 한쪽이 독자적으로 문항 데이터를 새로 만들거나
   고치지 말 것. 스키마를 바꾸려면 두 트랙 모두에 영향이 가니 이 문서에
   먼저 기록.
2. **수식 원본은 항상 raw LaTeX로 보존.** 트랙 1이 mathuit용으로 변환
   (mathify 또는 MathJax)하든, 트랙 2가 LaTeX 그대로 재사용하든, 원본
   `body`/`ch`/`sol`의 LaTeX 자체를 트랙별로 다르게 고쳐 쓰지 말 것 —
   변환은 각 트랙의 렌더러 레이어에서만.
3. **"오답을 다시 보여주는 방법"은 지금은 트랙 2(LaTeX 재조판)만 존재.**
   트랙 1의 quiz 렌더링이 완성되고 나면, 오답 필터링을 mathuit 안에서
   바로 하는 세 번째 방법이 생길 수 있다 — 이건 트랙 2를 대체하자는
   얘기가 아니라 사용자가 이미 "병행"으로 확정했으므로, 향후 세션이
   임의로 트랙 2를 걷어내지 말 것. 두 방법을 합칠지는 별도 결정 필요.
4. **새로 이 영역을 만지는 세션은 이 문서부터 갱신할 것.** 브랜치별로
   각자 인수인계 문서를 새로 쓰지 말고, 이 파일(`docs/주간지_mathuit_통합_인수인계.md`,
   `climath-app` 저장소, main 이관 예정)을 계속 고쳐 쓸 것.

---

## 4. 별개로 열려 있는 미해결 항목 (참고용, 위 두 트랙과 직접 무관)

- **C9 (RLS)**: `students`·`attendance` 테이블 RLS 꺼짐. 앱이 delete를
  실제로 쓰기 때문에(학생 삭제·이름변경) 단순 "DELETE 차단"은 앱을
  깨뜨림. 실제 선택지 3안: Netlify 사이트 비밀번호 / Supabase Auth 전환 /
  쓰기만 인증 분리. 미결정.
- **보안 사고 이력**: `climath-app`(public) 저장소에 한때 학생 실명이 든
  문서가 약 24분 노출된 이력 있음. 삭제는 했으나 히스토리 재작성(force-push)
  은 classifier에 막혀 미완 — 문제 커밋 SHA로는 여전히 접근 가능. 저장소
  소유자 판단 필요.
- **앱 설치 문제**: "환경 쪽"(이미 설치됨/iOS Safari 등)으로 결론 —
  앱 코드 자체는 정상. `sw.js` 수정은 불필요(초기 오진이었던 것 철회함).

---

## 부록 — 원문 위치 (superseded, 삭제 안 함)

- 트랙 1 원문: `climath-app@claude/work-preparation-xpb5nj:docs/주간지_mathuit_통합_인수인계.md`
- 트랙 2 원문: 대시보드 세션이 업로드한 `Mathuit_주간지_통합인수인계.md`
  (저장소에는 미커밋 상태였음 — 이 문서로 흡수 완료)
