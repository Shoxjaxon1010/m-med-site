// M-MED Service Worker — network-first strategy
// Versiyani o'zgartirsangiz, eski kesh tozalanadi
const CACHE_NAME = 'mmed-v2';

self.addEventListener('install', event => {
  // Yangi SW darhol faollashadi
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  // Eski versiyali keshlarni o'chiramiz
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  // Faqat GET so'rovlar
  if (event.request.method !== 'GET') return;

  event.respondWith(
    // Avval tarmoqdan (eng yangi versiya)
    fetch(event.request)
      .then(response => {
        // Muvaffaqiyatli javobni keshga saqlaymiz
        const copy = response.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
        return response;
      })
      .catch(() => {
        // Internet yo'q bo'lsa — keshdan beramiz
        return caches.match(event.request);
      })
  );
});
