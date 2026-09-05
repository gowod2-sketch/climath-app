#!/usr/bin/env python3
"""전체 게이트를 돌리고 통과하면 배포한다.

배포는 판단이 아니라 절차다. "이걸 올려도 되나"를 사람에게 묻는 대신
규칙으로 막는다. 규칙에 걸리면 배포하지 않고 이유를 말한다.

  python3 tools/ship.py              게이트만 (배포 안 함)
  python3 tools/ship.py --deploy     통과 시 실제 배포
"""
import glob, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(ROOT)
# _workspace/ 의 정본 위치는 mathuit/_workspace/ 다 (저장소 루트가 아니다).
# 예전에 이 상수가 REPO 기준으로 잘못 잡혀 있어, 저장소 루트에 남아 있던
# 옛 회차의 _workspace/(이미 해소된 에스컬레이션이 문서에는 그대로 적힌 채
# 남은 파일)를 "최신 인벤토리"로 잘못 읽어 배포를 막은 적이 있다.
WS = os.path.join(ROOT, '_workspace')

def sh(cmd, cwd=None):
    return subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)

def gate():
    """배포를 막아야 하는 조건들. 통과하면 [] 를 돌려준다."""
    blocks = []

    # 1) 형식·데이터 — check.py 가 본다 (내부에서 build.py를 실행해 index.html을 재생성한다)
    r = subprocess.run([sys.executable, 'tools/check.py'], cwd=ROOT,
                       capture_output=True, text=True)
    if r.returncode != 0:
        blocks.append(('콘텐츠 검증 실패', r.stdout.strip()))

    # 1.5) index.html이 재생성 후에도 커밋된 것과 다르면, content/*.md는 고쳤는데
    #    build.py로 다시 만든 index.html을 커밋에 안 넣은 것이다. 실제로 한 번
    #    있었다 — 소스 md는 고쳤지만 index.html의 DATA는 예전 값 그대로 배포될
    #    뻔했다. git diff로 감지한다(ROOT는 mathuit/, index.html은 그 바로 아래).
    d = sh("git diff --quiet -- index.html", ROOT)
    if d.returncode != 0:
        blocks.append(('index.html이 최신 content/*.md와 어긋난다 — build.py 재실행 후 다시 커밋할 것', ''))

    # 2) 화면 — 데이터가 맞아도 그려진 결과는 다를 수 있다.
    #    shoot.py 가 각 화면을 검사해 파손을 ⚠ 로 표시한다.
    r = subprocess.run([sys.executable, 'tools/shoot.py', '--all'], cwd=ROOT,
                       capture_output=True, text=True, timeout=600)
    bad = [ln.strip() for ln in (r.stdout or '').splitlines() if '⚠' in ln]
    if bad:
        blocks.append(('화면 파손 %d건' % len(bad), '\n'.join('  ' + b for b in bad)))
    elif r.returncode != 0:
        blocks.append(('화면 확인 실패 — 크롬을 못 찾았거나 캡처가 죽었다',
                       (r.stdout or r.stderr).strip()[-400:]))

    # 3) 계획 대비 누락 — 단원을 반쯤 출고하면 근거 사슬이 끊긴다.
    #    실제로 c14 가 빠진 채 c15 가 나가서, c15 본문이 근거로 삼는
    #    극한을 설명할 화면이 앱에 하나도 없는 상태가 됐다.
    inv = sorted(glob.glob(os.path.join(WS, '01_*inventory*.md')))
    if inv:
        txt = open(inv[-1], encoding='utf-8').read()
        m = re.search(r'^## 개념 목록(.*?)^## ', txt, re.S | re.M)
        planned = sorted(set(re.findall(r'c\d+\.md', m.group(1)))) if m else []
        made = set(os.path.basename(p) for p in glob.glob(os.path.join(ROOT, 'content/concept/c*.md')))
        missing = [f for f in planned if f not in made]
        present = [f for f in planned if f in made]
        # 막아야 하는 것은 **부분 출고**다. 계획의 일부만 있으면 근거 사슬이 끊긴다.
        # 하나도 없으면 이 브랜치가 그 단원을 손대지 않은 것이므로 막을 이유가 없다.
        # (_workspace/ 는 gitignore 대상이라 브랜치를 바꿔도 남는다 — 브랜치 상태가
        #  아니라 작업 디렉토리 상태이므로, 실제 파일 존재로 판정해야 한다.)
        if missing and present:
            blocks.append(('단원을 반쯤 출고하려 한다 — 근거 사슬이 끊긴다',
                           '  있음: %s\n  없음: %s\n  인벤토리: %s' % (
                               ' '.join(present), ' '.join(missing), os.path.basename(inv[-1]))))

    # 4) 미해결 에스컬레이션 — 그 단원을 실제로 출고하려 할 때만 본다
    if inv and 'present' in dir() and present:
        txt = open(inv[-1], encoding='utf-8').read()
        # 다음 '## ' 헤더 앞에서 멈춘다 — 안 그러면 이후의 다른 절(예: 오케스트레이터
        # 결정, 1차 에스컬레이션 처리 현황)까지 전부 이 절로 오인해 스캔한다.
        m = re.search(r'^## 에스컬레이션\s*\n(.*?)(?=^## |\Z)', txt, re.S | re.M)
        if m and m.group(1).strip() and '없음' not in m.group(1)[:40]:
            # 번호가 굵게 표시된 항목(**1. ...**)도 같은 항목이니 함께 센다.
            n = len(re.findall(r'^\**\d+\.', m.group(1), re.M))
            if n: blocks.append(('미해결 에스컬레이션 %d건 — 사람 결정 대기' % n, ''))

    # 5) 푸시 안 된 커밋
    a = sh("git rev-list --count @{u}..HEAD", REPO)
    if a.returncode == 0 and a.stdout.strip() not in ('', '0'):
        blocks.append(('푸시되지 않은 커밋 %s개' % a.stdout.strip(), ''))

    return blocks

def main():
    print("=== 배포 게이트 ===")
    blocks = gate()
    if blocks:
        print("\n배포하지 않습니다. 막는 이유 %d건:\n" % len(blocks))
        for title, detail in blocks:
            print("  ✗ " + title)
            if detail: print(detail)
        print("\n이건 판단이 아니라 규칙입니다. 조건을 해소하면 자동으로 통과합니다.")
        return 1

    print("  통과 — 막는 조건 없음")
    if '--deploy' not in sys.argv:
        print("\n실제 배포하려면: python3 tools/ship.py --deploy")
        return 0

    if sh("which netlify").returncode != 0:
        print("\n배포하려면 netlify CLI 가 필요합니다:")
        print("  npm i -g netlify-cli && netlify login && netlify link")
        return 2
    print("\n=== 배포 ===")
    r = sh("netlify deploy --prod --dir=dist", ROOT)
    print(r.stdout[-1200:] or r.stderr[-1200:])
    if r.returncode != 0:
        return r.returncode

    # 배포했다고 도달한 것이 아니다 — 실제로 확인한다.
    print("\n=== 도달 확인 ===")
    subprocess.run([sys.executable, 'tools/deploy_status.py'], cwd=ROOT)
    return 0

if __name__ == '__main__':
    sys.exit(main())
