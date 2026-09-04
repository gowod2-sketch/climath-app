---
name: mathuit-build-gate
description: "이 저장소에서 cd mathuit && python3 build.py 를 돌려 콘텐츠 문법과 팁 링크 정합성을 검증하고, 실패 메시지를 어느 파일의 무엇을 고쳐야 하는지로 번역하는 절차. mathuit 콘텐츠를 수정한 뒤 검증하거나 빌드 실패 원인을 찾을 때만 사용한다."
---

# mathuit 빌드 검증

`build.py`는 배포 게이트다. 실패하면 Netlify 빌드도 같은 지점에서 멈추므로 깨진 앱이 라이브로 나가지 않는다.

```bash
cd mathuit && python3 build.py
```

## 합격선

| 대상 | 조건 | 실패 메시지 |
|------|------|-----------|
| front matter | `---`로 시작하고 `---`로 닫힘 | `맨 위에 --- 로 시작하는 설정 블록이 필요합니다` |
| front matter | `키: 값` 형식 | `설정은 "키: 값" 형식이어야 합니다` |
| concept | `no, title, unit, sec` 존재 | `{키} 가 없습니다` |
| concept | `$$ 수식 $$` 존재 | `$$ 수식 $$ 이 없습니다` |
| tip | `title, oneline` 존재 | `{키} 가 없습니다` |
| tip | `## graph` 블록 존재 | `## graph 블록이 없습니다` |
| tip | `## steps` 블록 존재 | `## steps 블록이 없습니다` |
| steps | `show` 칸이 정수 | `show 칸은 숫자여야 합니다` |
| steps | 1줄 이상 | `스텝이 한 줄도 없습니다` |
| steps | **5줄 이하** | `스텝은 5개까지만 (지금 N개)` |
| 링크 | 모든 `[[id\|...]]`에 `tip/{id}.md` 존재 | `연결된 팁개념 파일이 없습니다` |

`kind: quiz` 개념은 `$$` 수식 검사를 건너뛴다.

## 한 번 통과가 전부 깨끗하다는 뜻은 아니다

`build.py`는 첫 에러에서 `sys.exit(1)`로 즉시 멈춘다. 뒤에 있는 에러는 아직 보이지도 않은 상태다.

**고친 뒤 반드시 재실행하라.** 통과가 나올 때까지 반복한다. 한 번 고치고 "됐다"고 넘어가면 다음 사람이 두 번째 에러를 받는다.

## 링크 정합성은 따로 봐야 한다

파일이 각각 멀쩡해도 concept의 링크 id와 tip 파일명이 어긋나면 실패한다. 이 불일치는 **파일을 하나씩 읽어서는 보이지 않는다.** 양쪽 목록을 뽑아 차집합을 구하라:

```bash
cd mathuit
grep -rhoE '\[\[[a-z0-9_]+' content/concept/ | sed 's/^\[\[//' | sort -u > /tmp/used.txt
ls content/tip/ | sed 's/\.md$//' | sort -u > /tmp/exist.txt
comm -23 /tmp/used.txt /tmp/exist.txt   # 링크했는데 파일 없음 → 빌드 실패 원인
comm -13 /tmp/used.txt /tmp/exist.txt   # 파일은 있는데 아무도 안 씀 → 고아 팁
```

## index.html이 함께 바뀐다

`build.py`는 검사만 하는 게 아니라 `index.html` 안의 `/*DATA:BEGIN*/` 데이터 블록을 갈아끼운다. 검증 목적으로 돌려도 **`index.html`이 수정된다.**

`git status`로 확인하고, 콘텐츠 변경과 함께 커밋할 것인지 판단하라. 내용이 동일하면 `주입: 변경 없음`이 출력되고 파일은 건드리지 않는다.

## 실패 보고 형식

원문을 그대로 옮기지 말고 담당까지 지정해서 넘겨라.

| 파일 | 에러 원문 | 해석 | 담당 |
|------|----------|------|------|
| `tip/deriv.md` | `스텝은 5개까지만 (지금 6개)` | 스토리보드 1컷 삭제 필요 | tip-author |
| `concept/c13.md` | `연결된 팁개념 파일이 없습니다` | `[[natlog]]` 링크의 tip 파일 부재 | tip-author 또는 링크 제거 |
