#!/usr/bin/env python3
"""mathuit 앱을 실제로 띄워 화면을 캡처한다.

build.py 도 check.py 도 데이터만 본다. 실제로 그려진 화면은 아무도 안 본다.
이 스크립트가 그 층이다.

사용:
  python3 tools/shoot.py              전체 개념 목록 출력
  python3 tools/shoot.py 2 6 12       해당 인덱스만 캡처
  python3 tools/shoot.py --all        전부 캡처

산출물: tools/_shots/  (gitignore 대상)
"""
import http.server, json, os, re, socketserver, subprocess, sys, threading, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_shots')
PORT = 0        # 0 = OS 가 빈 포트를 잡아준다 (충돌 방지)

# 헤드리스 크롬은 창 폭을 500px 아래로 못 내린다. 390 을 줘도 뷰포트는 500 이
# 되고 이미지만 잘린다 — 잘림을 앱 버그로 오해하기 쉬우니 500 을 하한으로 쓴다.
VIEW_W, VIEW_H = 500, 900

CHROME_CANDIDATES = [
    '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
    '/usr/bin/chromium', '/usr/bin/chromium-browser', '/usr/bin/google-chrome',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
]

def find_chrome():
    for p in CHROME_CANDIDATES:
        if os.path.exists(p): return p
    for name in ('chromium', 'google-chrome', 'chrome'):
        p = subprocess.run(['which', name], capture_output=True, text=True)
        if p.returncode == 0: return p.stdout.strip()
    return None

def pages():
    """실제 화면 순서. content-data.json 순서와 다를 수 있다 —
    index.html 이 콘텐츠에 퀴즈가 없으면 샘플 퀴즈를 splice 로 끼워 넣는다."""
    src = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
    d = json.loads(re.search(r'/\*DATA:BEGIN\*/\s*var DATA=(.*?);\s*/\*DATA:END\*/', src, re.S).group(1))
    out = [(p['no'], p['title']) for p in d['pages']]
    m = re.search(r"PAGES\.splice\((\d+),\s*0,\s*\{[^}]*?no:'([^']+)'[^}]*?title:'([^']+)'", src)
    if m:
        out.insert(int(m.group(1)), (m.group(2) + ' (하드코딩)', m.group(3)))
    return out

def make_probe(idx, pop=''):
    """목차 항목을 실제로 클릭해 이동한다. settle() 은 전역이 아니라 못 부른다."""
    src = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
    js = """
    var t=setInterval(function(){
      var el=document.querySelector('[data-go="%d"]'); if(!el) return;
      clearInterval(t); el.click();
      setTimeout(function(){
        var sheets=document.querySelectorAll('.sheet');
        var cur=sheets[%d], txt='?', flags=[];
        if(cur){
          var k=cur.querySelector('.kicker'); if(k) txt=k.textContent;
          var body=cur.textContent||'';
          if(body.indexOf('[[')>=0) flags.push('죽은링크');
          if(/&#[0-9]+;|&minus;/.test(body)) flags.push('엔티티노출');
          var pill=document.getElementById('pill'), sec=document.getElementById('sec');
          if(pill&&sec&&sec.textContent.trim().slice(-3)==='...') flags.push('헤더잘림');
        }
        document.title='SHOT '+txt+(flags.length?'  ⚠ '+flags.join(','):'');
        var key='%s';
        if(key){var tm=cur&&cur.querySelector('[data-t="'+key+'"]'); if(tm) tm.click();}
      },700);
    },100);
    """ % (idx, idx, pop)
    name = os.path.join(ROOT, '_probe.html')
    open(name, 'w', encoding='utf-8').write(
        src.replace('</body>', "\n<script>window.addEventListener('load',function(){%s});</script>\n</body>" % js))
    return name

def main():
    ps = pages()
    args = [a for a in sys.argv[1:]]
    if not args:
        print("화면 순서 (하드코딩 퀴즈 포함):")
        for i, (no, title) in enumerate(ps):
            print("  %2d  %-16s %s" % (i, no, title))
        print("\n캡처하려면: python3 tools/shoot.py 2 6 12   또는  --all")
        return 0

    chrome = find_chrome()
    if not chrome:
        print("크롬을 찾지 못했습니다. CHROME_CANDIDATES 에 경로를 추가하세요.")
        return 1

    targets = range(len(ps)) if '--all' in args else [int(a) for a in args if a.isdigit()]
    subprocess.run([sys.executable, 'build.py'], cwd=ROOT, capture_output=True)
    os.makedirs(SHOTS, exist_ok=True)

    os.chdir(ROOT)
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.TCPServer(("", PORT), Quiet)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    time.sleep(0.5)
    try:
        for i in targets:
            probe = make_probe(i)
            out = os.path.join(SHOTS, 'p%02d.png' % i)
            r = subprocess.run([chrome, '--headless', '--disable-gpu', '--no-sandbox',
                                '--hide-scrollbars', '--window-size=%d,%d' % (VIEW_W, VIEW_H),
                                '--virtual-time-budget=8000', '--dump-dom',
                                '--screenshot=' + out,
                                'http://localhost:%d/_probe.html' % port],
                               capture_output=True, text=True, timeout=90)
            got = re.search(r'<title>([^<]*)</title>', r.stdout or '')
            print("  %2d  %-16s → %s   %s" % (i, ps[i][0], os.path.basename(out),
                                              got.group(1) if got else '?'))
            os.remove(probe)
    finally:
        srv.shutdown()
    print("\n캡처 위치: %s" % SHOTS)
    print("눈으로 확인할 것: 대괄호 [[ 노출 · &#숫자; 노출 · 긴 단원명에서 헤더 깨짐")
    return 0

if __name__ == '__main__':
    sys.exit(main())
