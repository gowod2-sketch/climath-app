const C='mathtip-v11';
self.addEventListener('install',e=>{self.skipWaiting();});
self.addEventListener('activate',e=>{e.waitUntil(self.clients.claim());});
self.addEventListener('fetch',e=>{
if(e.request.method!=='GET')return;
e.respondWith(caches.open(C).then(c=>c.match(e.request).then(r=>{
const n=fetch(e.request).then(res=>{c.put(e.request,res.clone());return res;}).catch(()=>r);
return r||n;})));});
