// Cache a fixed connection notice only. Never cache app HTML, policy responses,
// submitted answers, documents, or an API error as an offline policy result.
const CACHE_PREFIX = 'jiwon-basket-offline-';
const CACHE_NAME = CACHE_PREFIX + 'v1';
const OFFLINE = '/offline.html';
const PAGES = new Set(['/', '/index.html', '/demo', '/demo/', '/demo/index.html']);

self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const response = await fetch(OFFLINE, {cache:'no-store', credentials:'omit'});
    if (!response.ok || !response.headers.get('content-type')?.includes('text/html')
        || !(await response.clone().text()).includes('data-offline-page="jiwon-basket"')) {
      throw new Error('offline notice unavailable');
    }
    await (await caches.open(CACHE_NAME)).put(OFFLINE, response);
    // Do not skip waiting: an active intake must not be reloaded automatically.
  })());
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(key => key.startsWith(CACHE_PREFIX) && key !== CACHE_NAME)
      .map(key => caches.delete(key)));
    await self.clients.claim();
  })());
});

self.addEventListener('message', event => {
  if (event.data?.type === 'APPLY_UPDATE') event.waitUntil(self.skipWaiting());
});

self.addEventListener('fetch', event => {
  const request = event.request, url = new URL(request.url);
  if (request.method !== 'GET' || request.mode !== 'navigate'
      || url.origin !== self.location.origin || !PAGES.has(url.pathname)) return;
  event.respondWith((async () => {
    try {
      // Keep online failures visible; only a failed network navigation falls back.
      return await fetch(request, {cache:'no-store'});
    } catch {
      const notice = await (await caches.open(CACHE_NAME)).match(OFFLINE);
      return notice || new Response('인터넷 연결 후 지원장바구니를 다시 열어 주세요.',
        {status:503, headers:{'Content-Type':'text/plain; charset=utf-8','Cache-Control':'no-store'}});
    }
  })());
});
