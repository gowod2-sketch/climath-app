// GitHub Contents API를 통해 concept/tip 마크다운 파일을 직접 commit합니다.
// editor.html에서 이 함수를 호출하면 git push 없이 저장 -> 커밋 -> (Netlify 자동감지) 배포까지 이어집니다.
//
// 필요한 환경변수 (Netlify 대시보드 > Site configuration > Environment variables):
//   GITHUB_TOKEN   - repo contents 쓰기 권한이 있는 GitHub PAT (fine-grained, Contents: Read and write)
//   GITHUB_REPO    - "gowod2-sketch/climath-app" (기본값으로 이미 설정되어 있음)
//   GITHUB_BRANCH  - "main" (기본값)

const REPO = process.env.GITHUB_REPO || 'gowod2-sketch/climath-app';
const BRANCH = process.env.GITHUB_BRANCH || 'main';
const API = 'https://api.github.com';

function json(status, body) {
  return {
    statusCode: status,
    headers: { 'Content-Type': 'application/json; charset=utf-8', 'Access-Control-Allow-Origin': '*' },
    body: JSON.stringify(body),
  };
}

// 파일명 검증: 영문 소문자/숫자/밑줄만, .md 확장자
function safeFilename(name) {
  return typeof name === 'string' && /^[a-z][a-z0-9_]*\.md$/.test(name);
}

function contentPath(type, filename) {
  const dir = type === 'concept' ? 'concept' : 'tip';
  return `mathuit/content/${dir}/${filename}`;
}

async function ghFetch(path, token, options = {}) {
  const res = await fetch(`${API}${path}`, {
    ...options,
    headers: {
      'Accept': 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  });
  return res;
}

exports.handler = async function (event) {
  if (event.httpMethod === 'OPTIONS') {
    return { statusCode: 204, headers: { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'GET, POST, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type' } };
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

    // 목록
    const dir = type === 'concept' ? 'concept' : 'tip';
    const res = await ghFetch(`/repos/${REPO}/contents/mathuit/content/${dir}?ref=${BRANCH}`, token);
    if (!res.ok) return json(res.status, { error: 'GitHub 목록 조회 실패', detail: await res.text() });
    const list = await res.json();
    const files = list.filter((f) => f.name.endsWith('.md') && !f.name.startsWith('_')).map((f) => f.name);
    return json(200, { files });
  }

  // --- POST: 파일 생성/수정 (commit) ---
  if (event.httpMethod === 'POST') {
    if (!token) return json(500, { error: 'GITHUB_TOKEN이 설정되지 않았습니다. Netlify 환경변수를 확인하세요.' });

    let body;
    try { body = JSON.parse(event.body); } catch (e) { return json(400, { error: '잘못된 요청 본문' }); }

    const { type, filename, content, message } = body;
    if (type !== 'concept' && type !== 'tip') return json(400, { error: 'type은 concept 또는 tip 이어야 합니다' });
    if (!safeFilename(filename)) return json(400, { error: '파일명은 영문 소문자로 시작하고 .md로 끝나야 합니다 (예: c02.md, converge.md)' });
    if (!content || typeof content !== 'string' || content.length < 10) return json(400, { error: '내용이 비어있습니다' });

    const path = contentPath(type, filename);

    // 기존 파일이면 sha가 있어야 업데이트 가능 (GitHub API 규칙)
    let sha;
    const existing = await ghFetch(`/repos/${REPO}/contents/${path}?ref=${BRANCH}`, token);
    if (existing.status === 200) {
      const data = await existing.json();
      sha = data.sha;
    } else if (existing.status !== 404) {
      return json(existing.status, { error: '기존 파일 조회 실패', detail: await existing.text() });
    }

    const commitMessage = message || `${sha ? '수정' : '추가'}: ${type} ${filename} (편집기에서 저장)`;
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
      commit: result.commit && result.commit.sha,
      htmlUrl: result.content && result.content.html_url,
      message: '저장되었습니다. Netlify가 자동으로 빌드를 시작합니다 (2~3분 소요).',
    });
  }

  return json(405, { error: '지원하지 않는 메서드입니다' });
};
