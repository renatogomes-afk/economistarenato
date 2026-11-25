const CACHE = 'fato67-v11';
const FILES = ['./', 'index.html', 'styles.css', 'app.js', 'data.js', 'config.js', 'extrato.js', 'nuvem.js', 'icon.svg', 'manifest.webmanifest', 'vendor/jszip.min.js', 'vendor/supabase.min.js'];
self.addEventListener('install', e => e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES))));
self.addEventListener('activate', e => e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))));
// Só arquivos do próprio app; chamadas ao Supabase passam direto (nunca do cache)
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET' || u.origin !== location.origin) return;
  e.respondWith(fetch(e.request).then(r => { if (r.ok) { const c = r.clone(); caches.open(CACHE).then(k => k.put(e.request, c)); } return r; }).catch(() => caches.match(e.request)));
});
