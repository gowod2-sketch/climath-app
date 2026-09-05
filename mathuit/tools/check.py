#!/usr/bin/env python3
"""mathuit 콘텐츠 검증 — build.py 가 잡지 못하는 것까지.

build.py 는 형식만 본다. 통과(exit 0)해도 화면이 깨져 있을 수 있다.
실제로 죽은 링크 2건과 엔티티 파손 6건이 3주 넘게 라이브에 있었고,
build.py 는 그동안 계속 초록불이었다.

단독 실행:  python3 tools/check.py
훅에서도 같은 것을 부른다.
"""
import json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'content-data.json')

def fail(msg, detail=''):
    print('  실패: %s' % msg)
    if detail: print(detail)
    return 1

def main():
    # 1) build.py — 형식·링크 정합성
    r = subprocess.run([sys.executable, 'build.py'], cwd=ROOT,
                       capture_output=True, text=True)
    if r.returncode != 0:
        return fail('build.py', r.stdout + r.stderr)
    print('  build.py 통과')

    if not os.path.exists(DATA):
        return fail('content-data.json 이 없습니다')
    d = json.load(open(DATA, encoding='utf-8'))

    bad = []

    # 2) 죽은 링크 — build.py 가 절대 못 잡는다.
    #    팁 id 에 SYM 문자열(sum, oo, alpha ...)이 들어가면 prose() 가
    #    링크를 만들기 전에 치환해 버려 data-t 가 생성조차 안 된다.
    #    그러면 "없는 팁" 검사 대상에도 없어 exit 0 이 나온다.
    for p in d['pages']:
        for f in ('p1', 'p2'):
            if '[[' in p.get(f, ''):
                bad.append('죽은 링크  %s %s' % (p['no'], f))

    # 3) 엔티티 파손 — &#8721; 같은 것이 문자 단위 span 에 갇히면
    #    브라우저가 엔티티로 해석하지 못해 코드가 글자로 보인다.
    for p in d['pages']:
        for f in ('p1', 'p2', 'eqL', 'eqR'):
            if '>&<' in p.get(f, '') or '>#<' in p.get(f, ''):
                bad.append('엔티티 파손  %s %s' % (p['no'], f))
    for k, t in d['tips'].items():
        if '>&<' in t.get('def', ''):
            bad.append('엔티티 파손  tip/%s oneline' % k)

    # 4) front matter title 은 변환을 타지 않는다 → 수식 표기가 날것으로 노출
    for p in d['pages']:
        if re.search(r'[A-Za-z0-9]\^|\\\\|\$\$', p.get('title', '')):
            bad.append('제목에 수식 표기  %s: %s' % (p['no'], p['title']))

    # 5) 고아 팁 — 아무 개념도 링크하지 않는 팁 (차단 아님, 보고만)
    used = set()
    for p in d['pages']:
        used |= set(re.findall(r'data-t="([a-z0-9_]+)"', p.get('p1','') + p.get('p2','')))
    for k, t in d['tips'].items():
        used |= set(t.get('rel', []))
    orphan = sorted(set(d['tips']) - used)

    if bad:
        print()
        for b in bad: print('  ' + b)
        print()
        print('  %d건. docs/harness/APP-BUGS.md 참조.' % len(bad))
        return 1

    print('  죽은 링크 0 · 엔티티 파손 0 · 제목 표기 정상')
    if orphan:
        print('  참고 — 아무도 안 쓰는 팁 %d개: %s' % (len(orphan), ' '.join(orphan)))
    return 0

if __name__ == '__main__':
    sys.exit(main())
