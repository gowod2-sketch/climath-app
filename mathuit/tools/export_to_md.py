#!/usr/bin/env python3
"""index.html에 하드코딩된 TIPS/PAGES를 content/*.md로 역추출합니다.

일회성 마이그레이션 도구입니다. 이미 있는 md는 덮어쓰지 않습니다(--force로 강제).
사용법:  python3 tools/export_to_md.py [--force] [--dry-run]
"""
import os, re, sys, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, 'index.html')
CONTENT = os.path.join(ROOT, 'content')

FORCE = '--force' in sys.argv
DRY = '--dry-run' in sys.argv

# ---------- HTML -> md 소스 역변환 ----------

# build.py의 SYM을 뒤집은 것 (긴 것부터)
UNSYM = [
    ('&minus;&#8734;', '-oo'),
    ('&#8594;', '->'), ('&#8804;', '<='), ('&#8805;', '>='),
    ('&#8800;', '!='), ('&#177;', '+-'), ('&#8943;', '...'),
    ('&#8721;', 'sum'), ('&#8734;', 'oo'),
    ('&#945;', 'alpha'), ('&#946;', 'beta'),
    ('&minus;', '-'), ('&nbsp;', ' '), ('&lt;', '<'), ('&gt;', '>'), ('&amp;', '&'),
    ('−∞', '-oo'), ('→', '->'), ('≤', '<='), ('≥', '>='), ('≠', '!='),
    ('±', '+-'), ('⋯', '...'), ('∑', 'sum'), ('∞', 'oo'), ('α', 'alpha'), ('β', 'beta'),
    ('−', '-'),
]

def unsym(t):
    for a, b in UNSYM:
        t = t.replace(a, b)
    return t

def strip_spans(t):
    """<span class="v">x</span> / <span class="m">x</span> 를 알맹이만 남깁니다."""
    prev = None
    while prev != t:
        prev = t
        t = re.sub(r'<span class="[vm]">(.*?)</span>', r'\1', t, flags=re.S)
    return t

def subsup(t):
    """<sub>n</sub> -> _n / _{ab},  <sup>2</sup> -> ^2 / ^{ab}"""
    def rep(m):
        tag, inner = m.group(1), m.group(2)
        inner = strip_spans(inner)
        sign = '_' if tag == 'sub' else '^'
        return sign + (inner if len(inner) == 1 else '{' + inner + '}')
    prev = None
    while prev != t:
        prev = t
        t = re.sub(r'<(sub|sup)[^>]*>(.*?)</\1>', rep, t, flags=re.S)
    return t

def html_to_md(t):
    """본문 HTML -> md 원문."""
    # 팁 링크 먼저 (안쪽 span 정리 포함)
    def term(m):
        tid, label = m.group(1), m.group(2)
        label = unsym(strip_spans(subsup(label)))
        return '[[%s|%s]]' % (tid, label)
    t = re.sub(r'<span class="term" data-t="([a-z0-9_]+)">(.*?)</span>', term, t, flags=re.S)
    t = subsup(t)
    t = strip_spans(t)
    t = unsym(t)
    t = re.sub(r'<[^>]+>', '', t)          # 남은 태그 제거
    t = re.sub(r'[ \t]+', ' ', t).strip()
    return t

def def_to_oneline(t):
    return html_to_md(t)

# ---------- index.html 파싱 ----------

def slice_block(src, start_pat, end_pat):
    a = re.search(start_pat, src)
    if not a:
        sys.exit('index.html에서 %s 를 찾지 못했습니다' % start_pat)
    b = re.compile(end_pat, re.M).search(src, a.end())
    if not b:
        sys.exit('index.html에서 %s 의 끝을 찾지 못했습니다' % start_pat)
    return src[a.end():b.start()]

def split_entries(block):
    """중괄호 깊이를 세어 최상위 항목들로 자릅니다."""
    out, depth, buf, instr, esc = [], 0, [], None, False
    for ch in block:
        if instr:
            buf.append(ch)
            if esc: esc = False
            elif ch == '\\': esc = True
            elif ch == instr: instr = None
            continue
        if ch in '"\'':
            instr = ch; buf.append(ch); continue
        if ch in '{[':
            depth += 1
        elif ch in '}]':
            depth -= 1
        if ch == ',' and depth == 0:
            out.append(''.join(buf)); buf = []; continue
        buf.append(ch)
    if ''.join(buf).strip():
        out.append(''.join(buf))
    return [e.strip() for e in out if e.strip()]

def jsfield(entry, name):
    """entry에서 name: '...' 또는 name: [...] 값을 원문 그대로 뽑습니다."""
    m = re.search(r'(?:^|[,{\s])' + name + r'\s*:\s*', entry)
    if not m:
        return None
    i = m.end()
    if entry[i] in '"\'':
        q = entry[i]; i += 1; buf = []; esc = False
        while i < len(entry):
            c = entry[i]
            if esc: buf.append(c); esc = False
            elif c == '\\': esc = True
            elif c == q: break
            else: buf.append(c)
            i += 1
        return ''.join(buf)
    if entry[i] in '[{':
        open_c, close_c = entry[i], (']' if entry[i] == '[' else '}')
        depth, j = 0, i
        while j < len(entry):
            if entry[j] == open_c: depth += 1
            elif entry[j] == close_c:
                depth -= 1
                if depth == 0: break
            j += 1
        return entry[i:j+1]
    j = i
    while j < len(entry) and entry[j] not in ',\n':
        j += 1
    return entry[i:j].strip()

def parse_tips(src):
    block = slice_block(src, r'var TIPS=\{', r'^\};$')
    tips = {}
    for entry in split_entries(block):
        m = re.match(r'([A-Za-z0-9_]+)\s*:\s*\{', entry)
        if not m:
            continue
        tid = m.group(1)
        body = entry[m.end()-1:]
        curve = None
        cm = re.search(r'seq\(function\(n\)\{return\s+(.*?);\}\)', body, re.S)
        if cm:
            curve = re.sub(r'\s+', ' ', cm.group(1)).strip()
        lines_raw = jsfield(body, 'lines') or '[]'
        try:
            lines = json.loads(lines_raw)
        except Exception:
            lines = []
        lab_raw = jsfield(body, 'lab') or '{}'
        lab_t = ''
        lab_a = 'end'
        tm = re.search(r"t\s*:\s*'((?:[^'\\]|\\.)*)'", lab_raw)
        if tm: lab_t = tm.group(1)
        am = re.search(r"a\s*:\s*'([a-z]+)'", lab_raw)
        if am: lab_a = am.group(1)
        steps_raw = jsfield(body, 'steps') or '[]'
        steps = []
        for s in split_entries(steps_raw[1:-1]):
            show = re.search(r'show\s*:\s*(\d+)', s)
            line = re.search(r'line\s*:\s*1', s)
            label = re.search(r'label\s*:\s*1', s)
            cap = re.search(r"caption\s*:\s*'((?:[^'\\]|\\.)*)'", s)
            steps.append({
                'show': int(show.group(1)) if show else 12,
                'line': 'v' if line else '',
                'label': 'v' if label else '',
                'caption': unsym(cap.group(1).replace("\\'", "'")) if cap else '',
            })
        tips[tid] = {
            'title': jsfield(body, 'title') or tid,
            'ic': jsfield(body, 'ic') or '',
            'def': jsfield(body, 'def') or '',
            'curve': curve or '60 + 80/n',
            'lines': lines,
            'label': lab_t,
            'label_at': {'end': 'right', 'start': 'left', 'middle': 'center'}.get(lab_a, 'right'),
            'steps': steps,
        }
    return tips

def parse_pages(src):
    block = slice_block(src, r'var PAGES=\[', r'^\];$')
    pages = []
    for entry in split_entries(block):
        if not entry.lstrip().startswith('{'):
            continue
        pages.append({
            'no': jsfield(entry, 'no') or '',
            'unit': jsfield(entry, 'unit') or '',
            'sec': jsfield(entry, 'sec') or '',
            'title': jsfield(entry, 'title') or '',
            'p1': jsfield(entry, 'p1') or '',
            'eqL': jsfield(entry, 'eqL') or '',
            'eqR': jsfield(entry, 'eqR') or '',
            'p2': jsfield(entry, 'p2') or '',
        })
    return pages

# ---------- REL(연관) ----------

def parse_rel(src):
    m = re.search(r'var REL=\{(.*?)\};', src, re.S)
    if not m:
        return {}
    rel = {}
    for km in re.finditer(r'([a-z0-9_]+)\s*:\s*\[([^\]]*)\]', m.group(1)):
        rel[km.group(1)] = [x.strip().strip("'\"") for x in km.group(2).split(',') if x.strip()]
    return rel

# ---------- md 쓰기 ----------

def write(path, text):
    if os.path.exists(path) and not FORCE:
        return 'skip'
    if DRY:
        return 'dry'
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    return 'write'

def tip_md(tid, t, rel):
    related = rel.get(tid, [])
    lines = ', '.join(str(x) for x in t['lines'])
    out = ['---',
           'title: %s' % t['title'],
           'icon: %s' % unsym(t['ic']),
           'oneline: %s' % def_to_oneline(t['def']),
           'related: [%s]' % ', '.join(related),
           '---', '', '## graph', '',
           'curve: %s' % t['curve'],
           'lines: [%s]' % lines]
    if t['label']:
        out += ['label: %s' % unsym(t['label']), 'label_at: %s' % t['label_at']]
    out += ['', '## steps', '',
            '| show | line | label | caption |',
            '|------|------|-------|---------|']
    for s in t['steps']:
        out.append('| %s | %s | %s | %s |' % (s['show'], s['line'], s['label'], s['caption']))
    return '\n'.join(out) + '\n'

def concept_md(p, order):
    eq = ('lim_{%s} %s' % (unsym(p['eqL']), html_to_md(p['eqR']))) if p['eqL'] else html_to_md(p['eqR'])
    return ('---\n'
            'no: %s\ntitle: %s\nunit: %s\nsec: %s\norder: %d\n'
            '---\n\n%s\n\n$$ %s $$\n\n%s\n') % (
        p['no'], p['title'], p['unit'], p['sec'], order,
        html_to_md(p['p1']), eq, html_to_md(p['p2']))

def concept_filename(p, order):
    m = re.search(r'(\d+)', p['no'])
    return 'c%02d.md' % (int(m.group(1)) if m else order)

def main():
    src = open(INDEX, encoding='utf-8').read()
    tips = parse_tips(src)
    pages = parse_pages(src)
    rel = parse_rel(src)
    print('index.html에서 팁개념 %d개, 개념 %d개를 읽었습니다.' % (len(tips), len(pages)))

    stats = {'write': 0, 'skip': 0, 'dry': 0}
    for tid, t in sorted(tips.items()):
        r = write(os.path.join(CONTENT, 'tip', tid + '.md'), tip_md(tid, t, rel))
        stats[r] += 1
        print('  tip/%s.md  %s' % (tid, r))
    for i, p in enumerate(pages, 1):
        fn = concept_filename(p, i)
        r = write(os.path.join(CONTENT, 'concept', fn), concept_md(p, i))
        stats[r] += 1
        print('  concept/%s  %s' % (fn, r))

    print('\n생성 %d개, 건너뜀 %d개%s' % (stats['write'], stats['skip'],
          (', dry-run %d개' % stats['dry']) if stats['dry'] else ''))
    if stats['skip'] and not FORCE:
        print('이미 있는 파일은 두었습니다. 덮어쓰려면 --force 를 붙이세요.')

if __name__ == '__main__':
    main()
