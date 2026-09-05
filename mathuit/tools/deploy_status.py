#!/usr/bin/env python3
"""배포가 실제로 사용자에게 도달했는지 확인한다.

build.py 가 통과했다고 배포된 것이 아니다. 실제로 이런 일이 있었다:
콘텐츠를 고치고 push 했는데 사이트가 git 에 연결돼 있지 않아 12일째
아무것도 나가지 않았고, 레포 문서는 "push하면 자동 배포됩니다"라고
적혀 있었다.

netlify CLI 가 필요하다:  npm i -g netlify-cli && netlify login
없으면 무엇을 수동으로 확인해야 하는지 알려준다.
"""
import json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(ROOT)

def sh(cmd, cwd=None):
    return subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)

def main():
    print("=== 이 저장소 ===")
    head = sh("git rev-parse --short HEAD", REPO).stdout.strip()
    branch = sh("git rev-parse --abbrev-ref HEAD", REPO).stdout.strip()
    print("  브랜치 %s  HEAD %s" % (branch, head))
    ahead = sh("git rev-list --count @{u}..HEAD", REPO)
    if ahead.returncode == 0 and ahead.stdout.strip() != '0':
        print("  ⚠ 푸시 안 된 커밋 %s개" % ahead.stdout.strip())

    print("\n=== netlify.toml 이 가리키는 사이트 ===")
    toml = os.path.join(REPO, 'netlify.toml')
    if os.path.exists(toml):
        first = open(toml, encoding='utf-8').readline().strip()
        print("  " + first)
        m = re.search(r'([a-z0-9-]+)\.netlify\.app', first)
        if m: print("  → 주석이 가리키는 이름: %s" % m.group(1))
        print("  주석은 낡을 수 있다. 아래 CLI 결과가 사실이다.")
    else:
        print("  netlify.toml 없음")

    if sh("which netlify").returncode != 0:
        print("""
=== netlify CLI 없음 — 수동으로 확인할 것 ===
  npm i -g netlify-cli && netlify login

  그 다음:
    netlify sites:list          살아 있는 사이트 목록
    netlify status              이 체크아웃이 어디에 링크됐는가

  대시보드에서 볼 것 (Site configuration → Build & deploy):
    - Repository 가 연결돼 있는가.  없으면 git push 로는 배포되지 않는다
    - Production branch 가 무엇인가
    - 마지막 배포 시각이 최신 커밋보다 뒤인가
""")
        return 2

    print("\n=== 사이트 목록 ===")
    r = sh("netlify sites:list --json")
    if r.returncode != 0:
        print("  실패: " + (r.stderr.strip()[:200] or "netlify login 이 필요할 수 있습니다"))
        return 2
    try:
        sites = json.loads(r.stdout)
    except Exception:
        print("  JSON 파싱 실패"); return 2

    for s in sites:
        name = s.get('name', '?')
        repo = (s.get('build_settings') or {}).get('repo_url')
        pub = s.get('published_deploy') or {}
        mark = "git 연결됨" if repo else "⚠ git 미연결 — push 로 배포되지 않음"
        print("  %-24s %s" % (name, mark))
        if repo: print("      %s  (branch: %s)" % (repo, (s.get('build_settings') or {}).get('repo_branch')))
        if pub:
            print("      마지막 배포 %s  commit %s" % (
                (pub.get('published_at') or '?')[:19], (pub.get('commit_ref') or '없음(수동 배포)')[:8]))
            if pub.get('commit_ref') and head and not pub['commit_ref'].startswith(head):
                print("      ⚠ 배포된 커밋이 현재 HEAD 와 다르다")
    print("\n판정: git 미연결 사이트는 콘텐츠를 아무리 고쳐도 사용자에게 도달하지 않는다.")
    return 0

if __name__ == '__main__':
    sys.exit(main())
