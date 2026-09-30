(function () {
  'use strict';

  if (window.__CD_EDITORIAL_META_READY) return;
  window.__CD_EDITORIAL_META_READY = true;

  function formatDate(value) {
    if (!value) return '30 September 2026';
    var d = new Date(value + 'T00:00:00');
    if (isNaN(d.getTime())) return '30 September 2026';
    return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' });
  }

  function findFactContainer() {
    return document.querySelector('.facts, .quick-facts');
  }

  function render(dateValue) {
    if (document.getElementById('cdEditorialMeta')) return;

    var facts = findFactContainer();
    if (!facts) return;

    var meta = document.createElement('div');
    meta.id = 'cdEditorialMeta';
    meta.className = 'cd-editorial-meta-static';
    meta.innerHTML =
      '<span class="cd-editorial-item"><span class="cd-editorial-icon" aria-hidden="true">▣</span>' +
      '<span><small>Last updated on</small><strong>' + formatDate(dateValue) + '</strong></span></span>' +
      '<span class="cd-editorial-divider" aria-hidden="true"></span>' +
      '<span class="cd-editorial-item"><span class="cd-editorial-icon" aria-hidden="true">●</span>' +
      '<span><small>Updated by</small><a href="/collegedecoded-team">CollegeDecoded Team</a></span></span>';

    facts.insertAdjacentElement('afterend', meta);

    var style = document.createElement('style');
    style.id = 'cdEditorialMetaStyles';
    style.textContent =
      '.cd-editorial-meta-static{width:min(1180px,calc(100% - 36px));margin:0 auto 18px;padding:14px 22px;background:linear-gradient(90deg,#fff8eb,#fffdf8);border:1px solid #f6d9ad;border-radius:12px;display:flex;align-items:center;justify-content:center;gap:34px;color:#334155;font:13px/1.45 Arial,Helvetica,sans-serif;box-shadow:0 2px 8px rgba(15,23,42,.035)}' +
      '.cd-editorial-item{display:flex;align-items:center;gap:11px;min-width:260px}' +
      '.cd-editorial-icon{width:36px;height:36px;border-radius:50%;display:grid;place-items:center;background:#ffedc9;color:#d97706;font-size:18px;font-weight:800;flex:0 0 36px}' +
      '.cd-editorial-item small{display:block;color:#64748b;font-size:11px;line-height:1.25;margin-bottom:2px}' +
      '.cd-editorial-item strong,.cd-editorial-item a{display:block;color:#123b78;font-size:14px;font-weight:800;text-decoration:none}' +
      '.cd-editorial-item a{color:#2563eb}' +
      '.cd-editorial-divider{width:1px;height:36px;background:#e9b56b;opacity:.85}' +
      '@media(max-width:640px){.cd-editorial-meta-static{width:calc(100% - 24px);margin:0 auto 12px;padding:11px 14px;gap:12px;justify-content:space-between;border-radius:10px}.cd-editorial-item{min-width:0;gap:7px;flex:1}.cd-editorial-icon{width:30px;height:30px;flex-basis:30px;font-size:14px}.cd-editorial-item small{font-size:9px}.cd-editorial-item strong,.cd-editorial-item a{font-size:10.5px}.cd-editorial-divider{height:28px}}' +
      '@media(max-width:380px){.cd-editorial-meta-static{padding:10px;gap:8px}.cd-editorial-item{gap:5px}.cd-editorial-icon{width:27px;height:27px;flex-basis:27px;font-size:12px}.cd-editorial-item strong,.cd-editorial-item a{font-size:9.5px}}';
    document.head.appendChild(style);
  }

  function getSitemapDate() {
    var current = window.location.pathname.replace(/\/$/, '');
    fetch('/sitemap.xml', { cache: 'no-store' })
      .then(function (res) { return res.ok ? res.text() : ''; })
      .then(function (xml) {
        var doc = new DOMParser().parseFromString(xml, 'application/xml');
        var urls = Array.prototype.slice.call(doc.getElementsByTagName('url'));
        for (var i = 0; i < urls.length; i++) {
          var loc = urls[i].getElementsByTagName('loc')[0];
          var lastmod = urls[i].getElementsByTagName('lastmod')[0];
          if (!loc || !lastmod) continue;
          var locPath = new URL(loc.textContent.trim(), window.location.origin).pathname.replace(/\/$/, '');
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