(function () {
  'use strict';

  if (window.__CD_EDITORIAL_META_READY) return;
  window.__CD_EDITORIAL_META_READY = true;

  function formatDate(value) {
    if (!value) return 'Sep 30, 2026';
    var d = new Date(value + 'T00:00:00');
    if (isNaN(d.getTime())) return 'Sep 30, 2026';
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  }

  function findInsertionPoint() {
    var main = document.querySelector('main');
    if (!main) return null;

    var children = Array.prototype.slice.call(main.children);
    var lastIntro = null;
    for (var i = 0; i < children.length; i++) {
      var el = children[i];
      if (el.matches && el.matches('.answer, .facts, .quick-facts, .hero-facts, .quick-facts-card')) {
        lastIntro = el;
        continue;
      }
      if (lastIntro) return { parent: main, before: el };
      return { parent: main, before: el };
    }
    return { parent: main, before: null };
  }

  function removeVisibleEscapedNewlines() {
    var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null);
    var nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    for (var i = 0; i < nodes.length; i++) {
      var node = nodes[i];
      var parent = node.parentElement;
      if (!parent || /^(SCRIPT|STYLE|NOSCRIPT|TEMPLATE)$/i.test(parent.tagName)) continue;
      if (/\\n/.test(node.nodeValue)) {
        node.nodeValue = node.nodeValue.replace(/(?:\\n\\s*)+/g, '');
      }
    }
  }

  function cleanUnwantedCusatLink(root) {
    var scope = root || document;
    var target = ['cusat', 'pg', 'mtech', '2026'].join(' ');
    function norm(value) {
      return (value || '').replace(/\\s+/g, ' ').trim().toLowerCase();
    }
    var links = scope.querySelectorAll ? scope.querySelectorAll('a') : [];
    for (var i = 0; i < links.length; i++) {
      if (norm(links[i].textContent) === target) links[i].remove();
    }
    var footer = document.querySelector('footer');
    if (footer) {
      var nodes = footer.querySelectorAll('span,p,li,div');
      for (var j = 0; j < nodes.length; j++) {
        if (norm(nodes[j].textContent) === target) nodes[j].remove();
      }
    }
  }

  function removeLegacyMeta() {
    var old = document.getElementById('cdEditorialMeta');
    if (old) old.remove();
    var oldStyle = document.getElementById('cdEditorialMetaStaticStyles');
    if (oldStyle) oldStyle.remove();
  }

  function render(dateValue) {
    // The homepage should not show editorial update metadata.
    var currentPath = window.location.pathname.replace(/\/$/, '');
    if (currentPath === '') {
      removeLegacyMeta();
      return;
    }
    removeLegacyMeta();
    cleanUnwantedCusatLink(document);
    if (document.querySelector('.cd-editorial-author')) return;

    var point = findInsertionPoint();
    if (!point) return;

    var meta = document.createElement('div');
    meta.className = 'cd-editorial-author';
    meta.innerHTML =
      '<div class="cd-editorial-avatar" aria-hidden="true">CD</div>' +
      '<div class="cd-editorial-copy">' +
        '<div class="cd-editorial-name"><a href="/collegedecoded-team">CollegeDecoded Team</a><span class="cd-editorial-verified" aria-label="Verified">✓</span></div>' +
        '<div class="cd-editorial-sub">Content Curator <span aria-hidden="true">|</span> Updated on - ' + formatDate(dateValue) + '</div>' +
      '</div>';

    if (point.before) point.parent.insertBefore(meta, point.before); else point.parent.appendChild(meta);

    var style = document.createElement('style');
    style.id = 'cdEditorialAuthorStyles';
    style.textContent =
      '.cd-editorial-author{width:100%;box-sizing:border-box;margin:14px 0 20px;padding:12px 16px;background:#fff;border:1px solid #edf0f5;border-radius:14px;display:flex;align-items:center;gap:11px;color:#475569;font:13px/1.35 Arial,Helvetica,sans-serif;box-shadow:0 2px 10px rgba(15,23,42,.035)}' +
      '.cd-editorial-avatar{width:36px;height:36px;border-radius:50%;display:grid;place-items:center;background:#ff6b1a;color:#fff;font-size:11px;font-weight:800;letter-spacing:.2px;flex:0 0 36px}' +
      '.cd-editorial-copy{min-width:0}' +
      '.cd-editorial-name{display:flex;align-items:center;gap:5px;line-height:1.15}' +
      '.cd-editorial-name a{color:#111827;font-size:15px;font-weight:800;text-decoration:none}' +
      '.cd-editorial-verified{width:15px;height:15px;border-radius:50%;display:inline-grid;place-items:center;background:#18a66a;color:#fff;font-size:10px;font-weight:900}' +
      '.cd-editorial-sub{margin-top:3px;color:#64748b;font-size:11.5px;font-weight:500}' +
      '.cd-editorial-sub span{padding:0 5px;color:#a1aab8}' +
      '@media(max-width:620px){.cd-editorial-author{margin:11px 0 16px;padding:10px 12px;border-radius:12px;gap:9px}.cd-editorial-avatar{width:32px;height:32px;flex-basis:32px;font-size:10px}.cd-editorial-name a{font-size:13px}.cd-editorial-sub{font-size:10px}.cd-editorial-sub span{padding:0 4px}}';
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
    document.addEventListener('DOMContentLoaded', function () {
      cleanUnwantedCusatLink(document);
      removeVisibleEscapedNewlines();
      getSitemapDate();
    });
  } else {
    cleanUnwantedCusatLink(document);
    removeVisibleEscapedNewlines();
    getSitemapDate();
  }

  new MutationObserver(function () {
    cleanUnwantedCusatLink(document);
    removeVisibleEscapedNewlines();
  }).observe(document.documentElement, { childList: true, subtree: true });
})();