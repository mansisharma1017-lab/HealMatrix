const CACHE_NAME = "healmatrix-v1";

const ASSETS_TO_CACHE = [
    "/",
    "/login",
    "/register",
    "/upgrade",

    /* Static files */
    "/static/manifest.json",
    "/static/css/style.css",
    "/static/js/language.js",

    /* Icons */
    "/static/icons/icon-64x64.png",
    "/static/icons/icon-128x128.png",
    "/static/icons/icon-192x192.png",
    "/static/icons/icon-512x512.png"
];

/* INSTALL */
self.addEventListener("install", event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS_TO_CACHE))
    );
    self.skipWaiting();
});

/* ACTIVATE */
self.addEventListener("activate", event => {
    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(keys.map(key => {
                if (key !== CACHE_NAME) {
                    return caches.delete(key);
                }
            }))
        )
    );
    self.clients.claim();
});

/* FETCH */
self.addEventListener("fetch", event => {
    event.respondWith(
        caches.match(event.request).then(response =>
            response || fetch(event.request)
        )
    );
});
