#!/usr/bin/env python3
"""content/*.md -> index.html 데이터 블록 생성기.

사용법:  python3 build.py
"""
import os, re, sys, json, html, zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(ROOT, 'content')
INDEX = os.path.join(ROOT, 'index.html')

SYM = [('-oo','&minus;&#8734;'), ('->','&#8594;'), ('<=','&#8804;'), ('>=','&#8805;'),
       ('!=','&#8800;'), ('+-','&#177;'), ('...','&#8943;'), ('sum','&#8721;'),
       ('oo','&#8734;'), ('alpha','&#945;'), ('beta','&#946;'), ('theta','&#952;')]

ROMAN_WORDS = {'lim','log','sin','cos','tan','ln','max','min'}

def err(msg, f=None):
    where = ' (%s)' % f if f else ''
    print('빌드 실패%s: %s' % (where, msg)); sys.exit(1)

def syms(t):
    for a,b in SYM:
        t = t.replace(a,b)
    return t

ENTITY = re.compile(r'&[#a-zA-Z0-9]+;')

def mathify(t):
    """변수는 이탤릭, 함수명/숫자/기호는 로만."""
    t = syms(t)
    out, i = [], 0
    while i < len(t):
        # syms()가 만든 HTML 엔티티(&#8721; 등)는 통째로 넘긴다.
        # 문자 단위로 쪼개면 각 글자가 span에 갇혀 엔티티로 해석되지 않고
        # 화면에 &#8721; 이 그대로 나온다.
        m = ENTITY.match(t[i:])
        if m:
            out.append('<span class="m">%s</span>' % m.group(0))
            i += len(m.group(0)); continue
        m = re.match(r'[A-Za-z]+', t[i:])
        if m:
            w = m.group(0)
            if w in ROMAN_WORDS:
                out.append('<span class="m">%s</span>' % w)
            else:
                out.append(''.join('<span class="v">%s</span>' % c for c in w))
            i += len(w); continue
        c = t[i]
        if c == '_' or c == '^':
            tag = 'sub' if c == '_' else 'sup'
            j = i+1
            if j < len(t) and t[j] == '{':
                k = t.find('}', j)
                inner = t[j+1:k]; i = k+1
            else:
                inner = t[j:j+1]; i = j+1
            out.append('<%s>%s</%s>' % (tag, mathify(inner), tag)); continue
        if c.isdigit() or c in '+=()[]|,.<>/&#;':
            out.append('<span class="m">%s</span>' % c); i += 1; continue
        out.append(c); i += 1
    return ''.join(out)

def prose(t):
    """본문: [[id|글자]] 링크 + 기호 + 단일 변수 이탤릭."""
    # 링크를 syms() 전에 빼둔다. sum/oo/alpha 같은 SYM 문자열이 팁 id에
    # 들어 있으면(예: sumval) syms()가 먼저 치환해 버려 링크 정규식에
    # 걸리지 않고, data-t 가 생성조차 안 된다. 그러면 빌드의 "없는 팁"
    # 검사에도 안 걸려 exit 0 인 채로 화면에 [[...]] 가 그대로 나온다.
    held = []
    def hold(m):
        held.append((m.group(1), m.group(2)))
        return '\x00%d\x00' % (len(held) - 1)
    t = re.sub(r'\[\[([a-z0-9_]+)\|([^\]]+)\]\]', hold, t)
    t = syms(t)
    # a_n, {a_n}, 단일 라틴 문자 -> 이탤릭
    # 링크와 엔티티는 건드리지 않는다. &minus; 의 m 이 이탤릭 처리되면
    # 엔티티가 깨져 화면에 &minus; 가 글자로 나온다.
    parts = re.split(r'(\x00\d+\x00|&[#a-zA-Z0-9]+;)', t)
    for i, p in enumerate(parts):
        if ENTITY.fullmatch(p): continue
        m = re.fullmatch(r'\x00(\d+)\x00', p)
        if m:
            tid, label = held[int(m.group(1))]
            parts[i] = '<span class="term" data-t="%s">%s</span>' % (tid, syms(label))
            continue
        parts[i] = re.sub(r'\b([A-Za-z])(_\{?[A-Za-z0-9]+\}?)?', lambda mm: mathify(mm.group(0)), p)
    return ''.join(parts)

def front(txt, f):
    if not txt.startswith('---'):
        err('맨 위에 --- 로 시작하는 설정 블록이 필요합니다', f)
    end = txt.find('\n---', 3)
    if end < 0: err('설정 블록이 --- 로 닫히지 않았습니다', f)
    meta = {}
    for line in txt[3:end].strip().splitlines():
        if not line.strip(): continue
        if ':' not in line: err('설정은 "키: 값" 형식이어야 합니다 -> %s' % line, f)
        k, v = line.split(':', 1)
        v = v.strip()
        if v.startswith('[') and v.endswith(']'):
            v = [x.strip() for x in v[1:-1].split(',') if x.strip()]
        meta[k.strip()] = v
    return meta, txt[end+4:]

def parse_tip(path):
    f = os.path.basename(path); tid = f[:-3]
    meta, body = front(open(path, encoding='utf-8').read(), f)
    for k in ('title','oneline'):
        if k not in meta: err('%s 가 없습니다' % k, f)
    # graph 는 선택이다. 수열 산점도로 표현되지 않는 개념(항등식, 식 변형,
    # 경우의 수, 행렬 ...)이 많아 필수로 두면 그런 팁은 아예 만들 수 없거나
    # 틀린 그림을 지어내게 된다. graph 가 없으면 steps 만으로 렌더한다.
    g = {}
    gm = re.search(r'##\s*graph(.*?)(?=##|\Z)', body, re.S)
    if gm:
        for line in gm.group(1).strip().splitlines():
            if ':' not in line: continue
            k, v = line.split(':', 1); g[k.strip()] = v.strip()
    sm = re.search(r'##\s*steps(.*?)(?=##|\Z)', body, re.S)
    if not sm: err('## steps 블록이 없습니다', f)
    steps = []
    for line in sm.group(1).strip().splitlines():
        if not line.strip().startswith('|'): continue
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if len(cells) < 4: continue
        if cells[0].lower() == 'show' or set(cells[0]) <= set('-: '): continue
        try: show = int(cells[0])
        except ValueError: err('show 칸은 숫자여야 합니다 -> %s' % line, f)
        steps.append({'show': show,
                      'line': 1 if cells[1].lower() in ('v','o','y','1') else 0,
                      'label': 1 if cells[2].lower() in ('v','o','y','1') else 0,
                      'caption': syms(cells[3])})
    if not steps: err('스텝이 한 줄도 없습니다', f)
    if len(steps) > 5: err('스텝은 5개까지만 (지금 %d개)' % len(steps), f)
    lines = json.loads(g.get('lines', '[]').replace("'", '"')) if g.get('lines') else []
    at = {'right': 'end', 'left': 'start', 'center': 'middle'}.get(g.get('label_at','right'), 'end')
    lx = {'end': 288, 'start': 30, 'middle': 160}[at]
    ly = (lines[0] - 8) if lines else 30
    return tid, {'title': meta['title'], 'cat': '팁개념', 'ic': syms(meta.get('icon','•')),
                 'def': prose(meta['oneline']), 'curve': g.get('curve', ''),
                 'lines': lines, 'lab': {'x': lx, 'y': ly, 'a': at, 't': syms(g.get('label',''))},
                 'steps': steps, 'rel': meta.get('related', []), 'nograph': not bool(gm)}

def parse_concept(path):
    f = os.path.basename(path)
    meta, body = front(open(path, encoding='utf-8').read(), f)
    for k in ('no','title','unit','sec'):
        if k not in meta: err('%s 가 없습니다' % k, f)
    if meta.get('kind') == 'quiz':
        options = []
        for i in range(1, 6):
            options.append(meta.get('option%d' % i, ''))
        return {'order': int(meta.get('order', 999)), 'no': meta['no'], 'unit': meta['unit'],
                'sec': meta['sec'], 'title': meta['title'], 'kind': 'quiz',
                'question': meta.get('question', ''), 'problemEq': meta.get('problemEq', ''),
                'options': options, 'answer': int(meta.get('answer', 1)),
                'sol': meta.get('sol', ''), 'src': meta.get('src', ''),
                'p1': '', 'p2': '', 'eqL': '', 'eqR': ''}
    m = re.search(r'\$\$(.*?)\$\$', body, re.S)
    if not m: err('$$ 수식 $$ 이 없습니다', f)
    before = body[:m.start()].strip()
    after = body[m.end():].strip()
    eq = m.group(1).strip()
    eqL, eqR = '', eq
    lm = re.match(r'lim_\{?([^}\s]+)\}?\s*(.*)', eq, re.S)
    if lm:
        eqL = syms(lm.group(1)); eqR = mathify(lm.group(2).strip())
    else:
        eqR = mathify(eq)
    return {'order': int(meta.get('order', 999)), 'no': meta['no'], 'unit': meta['unit'],
            'sec': meta['sec'], 'title': meta['title'],
            'p1': prose(before), 'p2': prose(after), 'eqL': eqL, 'eqR': eqR}

def main():
    if not os.path.isdir(CONTENT): err('content 폴더가 없습니다')
    tips = {}
    for fn in sorted(os.listdir(os.path.join(CONTENT,'tip'))):
        if fn.endswith('.md') and not fn.startswith('_'):
            k, v = parse_tip(os.path.join(CONTENT,'tip',fn)); tips[k] = v
    pages = []
    for fn in sorted(os.listdir(os.path.join(CONTENT,'concept'))):
        if fn.endswith('.md') and not fn.startswith('_'):
            pages.append(parse_concept(os.path.join(CONTENT,'concept',fn)))
    pages.sort(key=lambda p: p['order'])

    missing = []
    for p in pages:
        for m in re.finditer(r'data-t="([a-z0-9_]+)"', p['p1'] + p['p2']):
            if m.group(1) not in tips: missing.append((p['no'], m.group(1)))
    for k, t in tips.items():
        for r in t['rel']:
            if r not in tips: missing.append((k, r))
    if missing:
        for a, b in missing: print('  %s -> 없는 팁개념 id: %s' % (a, b))
        err('연결된 팁개념 파일이 없습니다 (위 목록)')

    print('팁개념 %d개, 개념 %d개 읽음' % (len(tips), len(pages)))
    out = os.path.join(ROOT, 'content-data.json')
    data = {'tips': tips, 'pages': pages}
    json.dump(data, open(out,'w',encoding='utf-8'), ensure_ascii=False, indent=1)
    print('중간 산출물:', out)

    inject(data)


BEGIN = '/*DATA:BEGIN*/'
END = '/*DATA:END*/'

def inject(data):
    """index.html의 DATA 마커 사이를 생성된 데이터로 갈아끼웁니다."""
    if not os.path.exists(INDEX):
        err('index.html이 없습니다')
    src = open(INDEX, encoding='utf-8').read()
    a = src.find(BEGIN)
    b = src.find(END)
    if a < 0 or b < 0 or b < a:
        err('index.html에서 %s ... %s 마커를 찾지 못했습니다' % (BEGIN, END))

    payload = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    # </script> 가 데이터 안에 들어가면 HTML 파싱이 깨지므로 escape
    payload = payload.replace('</', '<\\/')
    block = BEGIN + '\nvar DATA=' + payload + ';\n' + END

    new = src[:a] + block + src[b+len(END):]
    if new == src:
        print('주입: 변경 없음 (내용 동일)')
        return
    with open(INDEX, 'w', encoding='utf-8', newline='\n') as f:
        f.write(new)
    print('주입 완료: index.html (%d bytes)' % len(new))

if __name__ == '__main__':
    main()
