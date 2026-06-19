/* Service Worker — Video Stream Player PWA v1.0 */

var CACHE_NAME = 'video-player-v1';

var PRECACHE_URLS = [
  '/static/player/manifest.json',
  '/static/player/icons/icon-192.svg',
  '/static/player/icons/icon-512.svg'
];

// Installation : prechargement du cache
self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function(cache) {
      return cache.addAll(PRECACHE_URLS);
    }).then(function() {
      return self.skipWaiting();
    })
  );
});

// Activation : nettoyage des anciens caches
self.addEventListener('activate', function(event) {
  event.waitUntil(
    caches.keys().then(function(cacheNames) {
      return Promise.all(
        cacheNames.filter(function(name) {
          return name !== CACHE_NAME;
        }).map(function(name) {
          return caches.delete(name);
        })
      );
    }).then(function() {
      return self.clients.claim();
    })
  );
});

// Interception des requetes : strategie Network First, fallback cache
self.addEventListener('fetch', function(event) {
  // Ne pas intercepter les appels API
  if (event.request.url.includes('/download/')) {
    return;
  }

  event.respondWith(
    fetch(event.request)
      .then(function(response) {
        // Mettre en cache les reponses valides
        if (response && response.status === 200 && response.type === 'basic') {
          var responseClone = response.clone();
          caches.open(CACHE_NAME).then(function(cache) {
            cache.put(event.request, responseClone);
          });
        }
        return response;
      })
      .catch(function() {
        // Fallback sur le cache en cas d'echec reseau
        return caches.match(event.request).then(function(cached) {
          return cached || new Response('Mode hors-ligne', { status: 503 });
        });
      })
  );
});
