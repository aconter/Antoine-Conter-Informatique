// sw.js
const CACHE = 'ac-informatique-v1';
const ASSETS = [
  '/', // si tu as un index.html à la racine
  '/styles.css',
  '/Antoine-CONTER-informatique-Logo.webp',
  '/fond_antoine_conter_informatique.webp',
  '/map-antoine-conter-informatique.webp',
  '/moi.webp',
  '/phone.webp',
  '/whatapp.webp',
  '/mail.webp',
  '/watch.webp'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

// Stratégie "stale-while-revalidate" simple pour GET
self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;

  e.respondWith(
    caches.match(req).then((cached) => {
      const fetchPromise = fetch(req).then((networkRes) => {
        if (networkRes && networkRes.status === 200 && networkRes.type === 'basic') {
          const resClone = networkRes.clone();
          caches.open(CACHE).then((cache) => cache.put(req, resClone));
        }
        return networkRes;
      }).catch(() => cached);

      return cached || fetchPromise;
    })
  );
});
