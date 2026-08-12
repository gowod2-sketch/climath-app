const C='mathtip-v15';
self.addEventListener('install',e=>{self.skipWaiting();});
self.addEventListener('activate',e=>{e.waitUntil(
  caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==C).map(k=>caches.delete(k))))
    .then(()=>self.clients.claim())
);});
self.addEventListener('fetch',e=>{
if(e.request.method!=='GET')return;
const u=new URL(e.request.url);
// 다른 출처와 서버리스 함수(편집기 API)는 캐시하지 않습니다.
if(u.origin!==self.location.origin)return;
if(u.pathname.startsWith('/.netlify/'))return;
e.respondWith(caches.open(C).then(c=>c.match(e.request).then(r=>{
const n=fetch(e.request).then(res=>{c.put(e.request,res.clone());return res;}).catch(()=>r);
return r||n;})));});
