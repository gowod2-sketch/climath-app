// GitHub Contents API를 통해 저장소 파일을 직접 commit합니다.
// editor.html에서 이 함수를 호출하면 git push 없이 저장 -> 커밋 -> (Netlify 자동감지) 배포까지 이어집니다.
//
// 필요한 환경변수 (Netlify 대시보드 > Site configuration > Environment variables):
//   GITHUB_TOKEN   - repo contents 쓰기 권한이 있는 GitHub PAT (fine-grained, Contents: Read and write)
//   EDITOR_SECRET  - 쓰기 요청을 인증하는 공유 비밀키. 길고 무작위한 문자열로.
//   GITHUB_REPO    - "gowod2-sketch/climath-app" (기본값)
//   GITHUB_BRANCH  - "main" (기본값)
//
// 보안 메모
//   이 함수는 공개 URL로 노출됩니다. EDITOR_SECRET이 없으면 모든 쓰기를 거부합니다(fail-closed).
//   읽기(GET)는 공개 저장소를 조회하는 것이라 별도 인증을 두지 않았습니다.

const REPO = process.env.GITHUB_REPO || 'gowod2-sketch/climath-app';
const BRANCH = process.env.GITHUB_BRANCH || 'main';
const API = 'https://api.github.com';

// 쓰기를 허용할 경로 접두사. 저장소 루트의 다른 프로젝트(package.json 등)는 건드릴 수 없습니다.
const ALLOWED_PREFIX = 'mathuit/';
// 쓰기를 허용할 확장자
const ALLOWED_EXT = ['.md', '.html', '.js', '.py', '.json', '.webmanifest', '.svg', '.toml', '.txt'];

function json(status, body) {
  return {
    statusCode: status,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Access-Control-Allow-Origin': '*',
      'Cache-Control': 'no-store',
    },
    body: JSON.stringify(body),
  };
}

// 타이밍 공격을 줄이기 위해 길이와 내용을 상수 시간에 가깝게 비교합니다.
function safeEqual(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string') return false;
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

// 콘텐츠 파일명 검증: 영문 소문자로 시작, .md 확장자
function safeFilename(name) {
  return typeof name === 'string' && /^[a-z][a-z0-9_]*\.md$/.test(name);
}

function contentPath(type, filename) {
  const dir = type === 'concept' ? 'concept' : 'tip';
  return `${ALLOWED_PREFIX}content/${dir}/${filename}`;
}

// 임의 경로 쓰기(코드 파일용) 검증
function validatePath(p) {
  if (typeof p !== 'string' || !p) return '경로가 없습니다';
  if (p.includes('..')) return '상위 경로(..)는 쓸 수 없습니다';
  if (p.startsWith('/') || /^[A-Za-z]:/.test(p)) return '절대경로는 쓸 수 없습니다';
  if (p.includes('\\')) return '경로 구분자는 / 만 씁니다';
  if (!p.startsWith(ALLOWED_PREFIX)) return `${ALLOWED_PREFIX} 아래 경로만 쓸 수 있습니다`;
  if (!ALLOWED_EXT.some((e) => p.toLowerCase().endsWith(e))) return '허용되지 않는 확장자입니다';
  if (p.split('/').some((seg) => seg === '' || seg === '.')) return '경로 형식이 올바르지 않습니다';
  return null;
}

async function ghFetch(path, token, options = {}) {
  return fetch(`${API}${path}`, {
    ...options,
    headers: {
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  });
}

exports.handler = async function (event) {
  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 204,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, X-Editor-Secret',
      },
    };
  }

  const token = process.env.GITHUB_TOKEN;

  // --- GET: 목록 조회 또는 기존 파일 읽기 (공개 저장소라 토큰 없이도 됨) ---
  if (event.httpMethod === 'GET') {
    const { type, filename } = event.queryStringParameters || {};
    if (type !== 'concept' && type !== 'tip') return json(400, { error: 'type은 concept 또는 tip 이어야 합니다' });

    if (filename) {
      if (!safeFilename(filename)) return json(400, { error: '파일명이 올바르지 않습니다' });
      const path = contentPath(type, filename);
      const res = await ghFetch(`/repos/${REPO}/contents/${path}?ref=${BRANCH}`, token);
      if (res.status === 404) return json(404, { error: '파일을 찾을 수 없습니다' });
      if (!res.ok) return json(res.status, { error: 'GitHub 조회 실패', detail: await res.text() });
      const data = await res.json();
      const content = Buffer.from(data.content, 'base64').toString('utf-8');
      return json(200, { filename, content, sha: data.sha });
    }

    const dir = type === 'concept' ? 'concept' : 'tip';
    const res = await ghFetch(`/repos/${REPO}/contents/${ALLOWED_PREFIX}content/${dir}?ref=${BRANCH}`, token);
    if (!res.ok) return json(res.status, { error: 'GitHub 목록 조회 실패', detail: await res.text() });
    const list = await res.json();
    const files = list.filter((f) => f.name.endsWith('.md') && !f.name.startsWith('_')).map((f) => f.name);
    return json(200, { files });
  }

  // --- POST: 파일 생성/수정 (commit) ---
  if (event.httpMethod === 'POST') {
    // 1) 인증 먼저. 비밀키가 설정돼 있지 않으면 아예 거부합니다.
    const secret = process.env.EDITOR_SECRET;
    if (!secret) {
      return json(503, {
        error: 'EDITOR_SECRET이 설정되지 않아 쓰기가 비활성 상태입니다. Netlify 환경변수를 확인하세요.',
      });
    }
    const given = event.headers['x-editor-secret'] || event.headers['X-Editor-Secret'];
    if (!safeEqual(given || '', secret)) {
      return json(401, { error: '비밀키가 올바르지 않습니다' });
    }

    if (!token) return json(500, { error: 'GITHUB_TOKEN이 설정되지 않았습니다.' });

    let body;
    try {
      body = JSON.parse(event.body);
    } catch (e) {
      return json(400, { error: '잘못된 요청 본문' });
    }

    const { type, filename, content, message, path: rawPath } = body;
    if (!content || typeof content !== 'string' || content.length < 1) {
      return json(400, { error: '내용이 비어있습니다' });
    }

    // 2) 경로 결정 — 콘텐츠 모드(type+filename) 또는 코드 모드(path)
    let path;
    let label;
    if (rawPath) {
      const err = validatePath(rawPath);
      if (err) return json(400, { error: err });
      path = rawPath;
      label = rawPath;
    } else {
      if (type !== 'concept' && type !== 'tip') return json(400, { error: 'type은 concept 또는 tip 이어야 합니다' });
      if (!safeFilename(filename)) {
        return json(400, { error: '파일명은 영문 소문자로 시작하고 .md로 끝나야 합니다 (예: c02.md, converge.md)' });
      }
      path = contentPath(type, filename);
      label = `${type} ${filename}`;
    }

    // 3) 기존 파일이면 sha가 있어야 업데이트 가능 (GitHub API 규칙)
    let sha;
    const existing = await ghFetch(`/repos/${REPO}/contents/${path}?ref=${BRANCH}`, token);
    if (existing.status === 200) {
      const data = await existing.json();
      sha = data.sha;
    } else if (existing.status !== 404) {
      return json(existing.status, { error: '기존 파일 조회 실패', detail: await existing.text() });
    }

    const commitMessage = message || `${sha ? '수정' : '추가'}: ${label} (편집기에서 저장)`;
    const putRes = await ghFetch(`/repos/${REPO}/contents/${path}`, token, {
      method: 'PUT',
      body: JSON.stringify({
        message: commitMessage,
        content: Buffer.from(content, 'utf-8').toString('base64'),
        branch: BRANCH,
        ...(sha ? { sha } : {}),
      }),
    });

    if (!putRes.ok) return json(putRes.status, { error: 'GitHub 커밋 실패', detail: await putRes.text() });
    const result = await putRes.json();
    return json(200, {
      ok: true,
      path,
      commit: result.commit && result.commit.sha,
      htmlUrl: result.content && result.content.html_url,
      message: '저장되었습니다. Netlify가 자동으로 빌드를 시작합니다 (2~3분 소요).',
    });
  }

  return json(405, { error: '지원하지 않는 메서드입니다' });
};
