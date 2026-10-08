const CACHE_NAME = 'aig-v2';

// v3: la app pasó a módulos ES + avatar 3D. Sin subir la versión, los

// clientes con la caché v2 servirían el app.js antiguo (script clásico) y la

// PWA no arrancaría hasta que el navegador detectara el cambio de sw.js.

const STATIC_CACHE = 'aig-static-v3';

const API_CACHE = 'aig-api-v3';



const STATIC_ASSETS = [

  '/',

  '/index.html',

  '/css/mobile.css',

  '/js/app.js',

  '/js/api.js',

  '/js/views.js',

  '/js/daniela-avatar.js',

  // Runtime del avatar. El .glb (3,1 MB) NO se pre-cachéa: se cachea en la

  // primera carga con cacheFirst, para no retrasar la instalación del SW.

  '/vendor/three/build/three.module.min.js',

  '/vendor/three/build/three.core.min.js',

  '/vendor/three/examples/jsm/loaders/GLTFLoader.js',

  '/vendor/three/examples/jsm/utils/BufferGeometryUtils.js',

  '/vendor/three/examples/jsm/libs/meshopt_decoder.module.js',

  '/vendor/three/examples/jsm/environments/RoomEnvironment.js',

  '/manifest.json'

];



self.addEventListener('install', (event) => {

  event.waitUntil(

    caches.open(STATIC_CACHE).then((cache) => {

      return cache.addAll(STATIC_ASSETS);

    })

  );

  self.skipWaiting();

});



self.addEventListener('activate', (event) => {

  event.waitUntil(

    caches.keys().then((keys) => {

      return Promise.all(

        keys

          .filter((key) => key !== STATIC_CACHE && key !== API_CACHE)

          .map((key) => caches.delete(key))

      );

    })

  );

  self.clients.claim();

});



self.addEventListener('fetch', (event) => {

  const url = new URL(event.request.url);



  // El visor God's Eye es una PANTALLA EN VIVO (SSE, Cesium de 22 MB,

  // telemetría cada pocos segundos). Meterlo en la caché del service worker

  // dejaría la pantalla congelada en una versión vieja y se comería la caché

  // con los ficheros de Cesium: se le cede directamente al navegador.

  if (url.pathname.startsWith('/gods-eye')) {

    return;

  }



  if (url.pathname.startsWith('/api/')) {

    event.respondWith(networkFirstStrategy(event.request));

  } else {

    event.respondWith(cacheFirstStrategy(event.request));

  }

});



async function cacheFirstStrategy(request) {

  const cached = await caches.match(request);

  if (cached) return cached;



  try {

    const response = await fetch(request);

    if (response.ok) {

      const cache = await caches.open(STATIC_CACHE);

      cache.put(request, response.clone());

    }

    return response;

  } catch (err) {

    return caches.match('/index.html');

  }

}



async function networkFirstStrategy(request) {

  try {

    const response = await fetch(request);

    if (response.ok) {

      const cache = await caches.open(API_CACHE);

      cache.put(request, response.clone());

    }

    return response;

  } catch (err) {

    const cached = await caches.match(request);

    if (cached) return cached;

    return new Response(JSON.stringify({ error: 'Offline' }), {

      status: 503,

      headers: { 'Content-Type': 'application/json' }

    });

  }

}



self.addEventListener('sync', (event) => {

  if (event.tag === 'sync-status') {

    event.waitUntil(syncServiceStatus());

  }

});



async function syncServiceStatus() {

  const clients = await self.clients.matchAll();

  clients.forEach((client) => {

    client.postMessage({ type: 'SYNC_COMPLETE' });

  });

}



self.addEventListener('push', (event) => {

  const data = event.data ? event.data.json() : {};

  const title = data.title || 'aig';

  const options = {

    body: data.body || 'New notification',

    icon: '/icons/icon-192.png',

    badge: '/icons/icon-192.png',

    vibrate: [100, 50, 100],

    data: data.url || '/',

    actions: [

      { action: 'open', title: 'Open' },

      { action: 'dismiss', title: 'Dismiss' }

    ]

  };

  event.waitUntil(self.registration.showNotification(title, options));

});



self.addEventListener('notificationclick', (event) => {

  event.notification.close();

  if (event.action === 'dismiss') return;

  event.waitUntil(

    self.clients.matchAll({ type: 'window' }).then((clients) => {

      for (const client of clients) {

        if (client.url.includes(self.location.origin) && 'focus' in client) {

          return client.focus();

        }

      }

      return self.clients.openWindow(event.notification.data || '/');

    })

  );

});

