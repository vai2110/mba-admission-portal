(function () {
  'use strict';

  if (window.__CD_EDITORIAL_META_READY) return;
  window.__CD_EDITORIAL_META_READY = true;

  function formatDate(value) {
    if (!value) return '29 September 2026';
    var d = new Date(value + 'T00:00:00');
    if (isNaN(d.getTime())) return '29 September 2026';
    return d.toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'long',
      year: 'numeric'
    });
  }

  function render(dateValue) {
    if (document.getElementById('cdEditorialMeta')) return;

    var hero = document.querySelector('.hero');
    if (!hero) return;

    var meta = document.createElement('div');
    meta.id = 'cdEditorialMeta';
    meta.className = 'cd-editorial-meta';
    meta.innerHTML =
      '<span class="cd-editorial-date">Last updated: <strong>' +
      formatDate(dateValue) +
      '</strong></span>' +
      '<span class="cd-editorial-separator" aria-hidden="true">·</span>' +
      '<span>By <a href="/collegedecoded-team" class="cd-editorial-author">CollegeDecoded Editorial Team</a></span>';

    hero.insertAdjacentElement('afterend', meta);

    var style = document.createElement('style');
    style.id = 'cdEditorialMetaStyles';
    style.textContent =
      '.cd-editorial-meta{width:min(1200px,calc(100% - 32px));margin:0 auto;padding:11px 0 7px;color:#64748b;font:12px/1.5 Arial,Helvetica,sans-serif;display:flex;align-items:center;gap:8px}' +
      '.cd-editorial-meta strong{color:#475569;font-weight:700}' +
      '.cd-editorial-meta a{color:#2563eb;font-weight:700;text-decoration:none}' +
      '.cd-editorial-meta a:hover{text-decoration:underline}' +
      '@media(max-width:560px){.cd-editorial-meta{width:calc(100% - 24px);padding:9px 0 5px;font-size:11px;gap:6px;flex-wrap:wrap}}';
    document.head.appendChild(style);
  }

  function getSitemapDate() {
    var path = window.location.pathname.replace(/\\/g, '/').replace(/\\/g, '');
    if (path === '/') return null;
    var clean = path.replace(/^\\//, '').replace(/\\/g, '');
    var candidates = [clean, clean.replace(/\\/$/, ''), clean + '.html'];

    fetch('/sitemap.xml', { cache: 'no-store' })
      .then(function (res) { return res.ok ? res.text() : ''; })
      .then(function (xml) {
        var doc = new DOMParser().parseFromString(xml, 'application/xml');
        var urls = Array.prototype.slice.call(doc.getElementsByTagName('url'));
        for (var i = 0; i < urls.length; i++) {
          var loc = urls[i].getElementsByTagName('loc')[0];
          var lastmod = urls[i].getElementsByTagName('lastmod')[0];
          if (!loc || !lastmod) continue;
          var locPath = new URL(loc.textContent.trim(), window.location.origin).pathname.replace(/\\/$/, '');
          var current = window.location.pathname.replace(/\\/$/, '');
          if (locPath === current) {
            render(lastmod.textContent.trim());
            return;
          }
        }
        render(null);
      })
      .catch(function () { render(null); });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', getSitemapDate);
  } else {
    getSitemapDate();
  }
})();