# climath-app

이 저장소에는 두 프로젝트가 함께 있습니다.

| 경로 | 프로젝트 |
|------|---------|
| `/` | climath-oap (React + Vite + Capacitor + Supabase) |
| `/mathuit` | Mathuit — 수열의 극한 PWA (Netlify 배포 대상) |

## 하네스: mathuit 수학 콘텐츠 파이프라인

**목표:** `docs/*.md` 수학 명세를 `mathuit/content/{concept,tip}/*.md` 앱 콘텐츠로 변환하고 `build.py` 게이트를 통과시킨다.

**트리거:** mathuit 콘텐츠 변환·추가·수정 작업 요청 시 `mathuit-content-pipeline` 스킬을 사용하라. 콘텐츠에 대한 단순 질문은 직접 응답해도 된다.

**실행 모드:** 서브 에이전트. `Agent` 도구로 직접 호출하고 반환값과 `_workspace/` 파일로 결과를 모은다.

**변경 이력:**
| 날짜 | 변경 내용 | 대상 | 사유 |
|------|----------|------|------|
| 2026-09-04 | 초기 구성 (에이전트 5, 스킬 4) | 전체 | — |

## 알려진 제약

팁개념 그래프는 **n=1..12 수열 산점도로 고정**입니다. 수열의 극한 단원(`concept/c01`~`c12`)에는 맞지만, 대기 중인 `docs/03_지수로그함수_미분.md`·`docs/04_삼각함수_덧셈정리.md`의 용어 상당수는 수열로 표현되지 않습니다. 이 경우 임의로 그래프를 지어내지 말고 에스컬레이션합니다 — 자세한 내용은 `.claude/skills/mathuit-tip-graph/SKILL.md` 참조.
