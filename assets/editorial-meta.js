(function () {
  'use strict';

  if (window.__CD_EDITORIAL_META_READY) return;
  window.__CD_EDITORIAL_META_READY = true;


  function injectGlobalHeroStandard() {
    if (document.getElementById('cdGlobalHeroStandardStyles')) return;
    if (!document.querySelector('.hero')) return;
    var style = document.createElement('style');
    style.id = 'cdGlobalHeroStandardStyles';
    style.textContent = "\n/* COLLEGEDECODED — GLOBAL HERO STANDARD\n   Scope: hero container sizing, spacing, typography and responsive layout only.\n   Do not change hero content, colors, navigation or page body content. */\n.cd-global-hero-standard,\n.hero{\n  box-sizing:border-box!important;\n}\n.hero{\n  height:145px!important;\n  min-height:145px!important;\n  max-height:145px!important;\n  padding:0!important;\n  display:flex!important;\n  align-items:center!important;\n  overflow:hidden!important;\n}\n.hero-container,\n.hero-inner,\n.hero-main,\n.hero-text{\n  box-sizing:border-box!important;\n  width:1180px!important;\n  max-width:calc(100% - 36px)!important;\n  margin:0 auto!important;\n}\n.hero-container,\n.hero-inner{\n  min-height:0!important;\n}\n.hero h1{\n  box-sizing:border-box!important;\n  font-family:Arial,Helvetica,sans-serif!important;\n  font-size:30px!important;\n  line-height:1.2!important;\n  font-weight:800!important;\n  letter-spacing:0!important;\n  margin:0 0 7px!important;\n  max-width:980px!important;\n  color:#fff!important;\n  display:-webkit-box!important;\n  -webkit-box-orient:vertical!important;\n  -webkit-line-clamp:2!important;\n  overflow:hidden!important;\n}\n.hero h2{\n  box-sizing:border-box!important;\n  font-family:Arial,Helvetica,sans-serif!important;\n  font-size:16px!important;\n  line-height:1.35!important;\n  font-weight:600!important;\n  margin:0 0 7px!important;\n  max-width:900px!important;\n  color:#dbeafe!important;\n  display:-webkit-box!important;\n  -webkit-box-orient:vertical!important;\n  -webkit-line-clamp:1!important;\n  overflow:hidden!important;\n}\n.hero p{\n  box-sizing:border-box!important;\n  font-family:Arial,Helvetica,sans-serif!important;\n  font-size:12px!important;\n  line-height:1.4!important;\n  margin:0 0 7px!important;\n  max-width:760px!important;\n  color:#dbeafe!important;\n}\n.hero-meta,\n.hero-location,\n.hero small{\n  box-sizing:border-box!important;\n  font-family:Arial,Helvetica,sans-serif!important;\n  font-size:11px!important;\n  line-height:1.4!important;\n  font-weight:700!important;\n  margin:0!important;\n  color:#dbeafe!important;\n}\n.hero a{font-family:Arial,Helvetica,sans-serif!important;}\n\n@media(max-width:720px){\n  .hero{\n    height:132px!important;\n    min-height:132px!important;\n    max-height:132px!important;\n  }\n  .hero-container,\n  .hero-inner,\n  .hero-main,\n  .hero-text{\n    width:100%!important;\n    max-width:calc(100% - 24px)!important;\n    margin:0 auto!important;\n  }\n  .hero h1{\n    font-size:24px!important;\n    line-height:1.2!important;\n    max-width:100%!important;\n    margin-bottom:6px!important;\n  }\n  .hero h2{\n    font-size:13px!important;\n    line-height:1.35!important;\n    max-width:100%!important;\n    margin-bottom:6px!important;\n  }\n  .hero p{\n    font-size:11px!important;\n    line-height:1.35!important;\n    max-width:100%!important;\n    margin-bottom:5px!important;\n  }\n  .hero-meta,\n  .hero-location,\n  .hero small{\n    font-size:10px!important;\n    line-height:1.35!important;\n  }\n}\n";
    document.head.appendChild(style);
  }

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
    injectGlobalHeroStandard();
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
      injectGlobalHeroStandard();
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