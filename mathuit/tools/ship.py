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
WS = os.path.join(REPO, '_workspace')

def sh(cmd, cwd=None):
    return subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)

def gate():
    """배포를 막아야 하는 조건들. 통과하면 [] 를 돌려준다."""
    blocks = []

    # 1) 형식·데이터 — check.py 가 본다
    r = subprocess.run([sys.executable, 'tools/check.py'], cwd=ROOT,
                       capture_output=True, text=True)
    if r.returncode != 0:
        blocks.append(('콘텐츠 검증 실패', r.stdout.strip()))

    # 2) 계획 대비 누락 — 단원을 반쯤 출고하면 근거 사슬이 끊긴다.
    #    실제로 c14 가 빠진 채 c15 가 나가서, c15 본문이 근거로 삼는
    #    극한을 설명할 화면이 앱에 하나도 없는 상태가 됐다.
    inv = sorted(glob.glob(os.path.join(WS, '01_*inventory*.md')))
    if inv:
        txt = open(inv[-1], encoding='utf-8').read()
        m = re.search(r'^## 개념 목록(.*?)^## ', txt, re.S | re.M)
        planned = sorted(set(re.findall(r'c\d+\.md', m.group(1)))) if m else []
        made = set(os.path.basename(p) for p in glob.glob(os.path.join(ROOT, 'content/concept/c*.md')))
        missing = [f for f in planned if f not in made]
        if missing:
            blocks.append(('계획된 개념 미생성 — 단원을 반쯤 출고하면 근거가 끊긴다',
                           '  누락: %s\n  인벤토리: %s' % (' '.join(missing), os.path.basename(inv[-1]))))

    # 3) 미해결 에스컬레이션
    if inv:
        txt = open(inv[-1], encoding='utf-8').read()
        m = re.search(r'^## 에스컬레이션(.*)', txt, re.S | re.M)
        if m and m.group(1).strip() and '없음' not in m.group(1)[:40]:
            n = len(re.findall(r'^\d+\.', m.group(1), re.M))
            if n: blocks.append(('미해결 에스컬레이션 %d건 — 사람 결정 대기' % n, ''))

    # 4) 푸시 안 된 커밋
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
    print(r.stdout[-1500:] or r.stderr[-1500:])
    return r.returncode

if __name__ == '__main__':
    sys.exit(main())
