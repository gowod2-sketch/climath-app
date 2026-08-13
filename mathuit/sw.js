const CACHE_NAME = 'mathtip-runtime-v16';

self.addEventListener('install', (event) => {
  event.waitUntil(self.skipWaiting());
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin || url.pathname.startsWith('/.netlify/')) return;

  // Network-first: 배포 직후에는 항상 최신 파일을 우선 사용하고,
  // 오프라인일 때만 마지막으로 성공한 응답을 사용한다.
  event.respondWith(
    fetch(event.request, { cache: 'no-store' })
      .then((response) => {
        if (response.ok) {
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, response.clone()));
        }
        return response;
      })
      .catch(() => caches.open(CACHE_NAME).then((cache) => cache.match(event.request)))
  );
});
