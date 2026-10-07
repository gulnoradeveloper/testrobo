{% load static %}/* BEGOYIM PWA service worker: statik fayllar keshi + oflayn sahifa. */
const CACHE = "begoyim-v1";
const ASSETS = [
  "{% url 'core:offline' %}",
  "{% static 'begoyim/css/begoyim.css' %}",
  "{% static 'eduwell/css/templatemo-eduwell-style.css' %}",
  "{% static 'vendor/bootstrap/css/bootstrap.min.css' %}",
  "{% static 'begoyim/img/logo-header.png' %}"
];
self.addEventListener("install", (e) => { e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS))); self.skipWaiting(); });
self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))));
});
self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  if (req.mode === "navigate") {
    e.respondWith(fetch(req).catch(() => caches.match("{% url 'core:offline' %}")));
    return;
  }
  if (req.url.includes("/static/")) {
    e.respondWith(caches.match(req).then((r) => r || fetch(req)));
  }
});
