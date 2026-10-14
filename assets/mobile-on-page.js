(function () {
  'use strict';
  if (window.__CD_MOBILE_ON_PAGE_V2) return;
  window.__CD_MOBILE_ON_PAGE_V2 = true;

  var STYLE_ID = 'cd-mobile-on-page-v2-style';
  var SCRIPT_VERSION = '20261014v3';

  function addStyles() {
    if (document.getElementById(STYLE_ID)) return;
    var style = document.createElement('style');
    style.id = STYLE_ID;
    style.textContent = [
      '.cd-mobile-on-page-v2{display:none;box-sizing:border-box;width:100%;max-width:none;margin:0;padding:0;position:fixed;top:0;right:8px;left:auto;z-index:1100;pointer-events:none;visibility:hidden}',
      '.cd-mobile-on-page-v2 details{position:relative;width:25vw;min-width:0;max-width:25vw;margin-left:auto;font:600 12px/1.35 Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#12336d;pointer-events:auto}',
      '.cd-mobile-on-page-v2 summary{list-style:none;cursor:pointer;display:flex;align-items:center;justify-content:space-between;gap:3px;width:100%;box-sizing:border-box;padding:9px 6px;border:1px solid #d8e3f3;border-radius:10px;background:#fff;box-shadow:0 3px 12px rgba(16,42,114,.08);font-weight:800;white-space:nowrap}',
      '.cd-mobile-on-page-v2 summary::-webkit-details-marker{display:none}',
      '.cd-mobile-on-page-v2 summary:after{content:"⌄";font-size:15px;line-height:1;transition:transform .15s ease}',
      '.cd-mobile-on-page-v2 details[open] summary:after{transform:rotate(180deg)}',
      '.cd-mobile-on-page-v2 nav{position:absolute;top:calc(100% + 6px);right:0;width:min(300px,90vw);max-height:min(60vh,420px);overflow:auto;display:flex;flex-direction:column;gap:2px;padding:7px;background:#fff;border:1px solid #dbe5f2;border-radius:12px;box-shadow:0 14px 35px rgba(16,42,114,.16)}',
      '.cd-mobile-on-page-v2 nav a{display:block;padding:10px 11px;border-radius:7px;color:#183b70;text-decoration:none;font-size:12px;line-height:1.4;font-weight:650}',
      '.cd-mobile-on-page-v2 nav a:hover,.cd-mobile-on-page-v2 nav a:focus{background:#eff5ff;outline:none}',
      '.cd-mobile-on-page-v2 nav:empty{display:none}',
      'html{scroll-padding-top:92px}',
      '[id].cd-onpage-target{scroll-margin-top:92px}',
      '@media(min-width:768px){.cd-mobile-on-page-v2{display:none!important}}',
      '@media(max-width:767px){.cd-mobile-on-page-v2{display:block;right:8px;top:0;visibility:hidden}.cd-mobile-on-page-v2.is-visible{visibility:visible}.cd-mobile-on-page-v2 details{width:25vw;max-width:25vw;min-width:0}}',
      '@media(max-width:360px){.cd-mobile-on-page-v2{padding-left:12px;padding-right:12px}.cd-mobile-on-page-v2 summary{font-size:10.5px;padding:8px 5px}}',
      '@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}.cd-mobile-on-page-v2 summary:after{transition:none}}'
    ].join('\n');
    document.head.appendChild(style);
  }

  function getHero() {
    return document.querySelector('.hero, .hero-section, header + section.hero, .hero-container') ||
      document.querySelector('header + section') ||
      document.querySelector('main .hero');
  }

  function getSectionLinks() {
    var links = [];
    var seen = {};
    var sourceLinks = document.querySelectorAll('.sidebar a[href^="#"], .sidebar-card a[href^="#"], .on-this-page a[href^="#"], .mobile-on-page a[href^="#"], .mobile-onpage a[href^="#"], .mobile-onpage nav a[href^="#"], .mobile-on-page nav a[href^="#"]');
    Array.prototype.forEach.call(sourceLinks, function (a) {
      var href = a.getAttribute('href') || '';
      var id = href.slice(1);
      if (!id || seen[id]) return;
      var target = document.getElementById(id);
      if (!target) return;
      seen[id] = true;
      links.push({ id: id, label: (a.textContent || '').replace(/\s+/g, ' ').trim() || (target.querySelector('h2,h3') || target).textContent.trim() });
    });
    if (!links.length) {
      var headings = document.querySelectorAll('main h2[id], main section[id] h2, main article h2, .content h2, main [id].main-section h2');
      Array.prototype.forEach.call(headings, function (h, index) {
        var target = h.id ? h : h.closest('[id]');
        if (!target || !target.id || seen[target.id]) return;
        var label = (h.textContent || '').replace(/\s+/g, ' ').trim();
        if (!label) return;
        seen[target.id] = true;
        links.push({ id: target.id, label: label });
      });
    }
    return links;
  }

  function findExistingNav() {
    return document.querySelector('.cd-mobile-on-page-v2, .mobile-on-page, .mobile-onpage, .mobile-on-page-nav');
  }

  function buildNav(links) {
    var wrap = document.createElement('div');
    wrap.className = 'cd-mobile-on-page-v2';
    wrap.setAttribute('aria-label', 'Page section navigation');
    var details = document.createElement('details');
    var summary = document.createElement('summary');
    summary.textContent = 'On this page';
    details.appendChild(summary);
    var nav = document.createElement('nav');
    nav.setAttribute('aria-label', 'Jump to section');
    links.forEach(function (item) {
      var a = document.createElement('a');
      a.href = '#' + encodeURIComponent(item.id);
      a.textContent = item.label;
      a.setAttribute('data-cd-section-id', item.id);
      nav.appendChild(a);
    });
    details.appendChild(nav);
    wrap.appendChild(details);
    return wrap;
  }

  function normalizeExistingNav(existing, links) {
    if (!existing) return buildNav(links);
    if (existing.classList.contains('cd-mobile-on-page-v2')) return existing;
    var details = existing.matches('details') ? existing : existing.querySelector('details');
    var source = details ? details.querySelectorAll('a[href^="#"]') : existing.querySelectorAll('a[href^="#"]');
    var wrap = buildNav([]);
    var nav = wrap.querySelector('nav');
    var seen = {};
    Array.prototype.forEach.call(source, function (a) {
      var href = a.getAttribute('href') || '';
      var id = href.slice(1);
      if (!id || seen[id] || !document.getElementById(decodeURIComponentSafe(id))) return;
      seen[id] = true;
      var link = document.createElement('a');
      link.href = '#' + encodeURIComponent(decodeURIComponentSafe(id));
      link.textContent = (a.textContent || '').replace(/\s+/g, ' ').trim() || id;
      link.setAttribute('data-cd-section-id', decodeURIComponentSafe(id));
      nav.appendChild(link);
    });
    if (!nav.children.length) {
      links.forEach(function (item) {
        var a = document.createElement('a');
        a.href = '#' + encodeURIComponent(item.id);
        a.textContent = item.label;
        a.setAttribute('data-cd-section-id', item.id);
        nav.appendChild(a);
      });
    }
    existing.replaceWith(wrap);
    return wrap;
  }

  function decodeURIComponentSafe(value) {
    try { return decodeURIComponent(value); } catch (e) { return value; }
  }

  function insertAfterHero(nav) {
    var hero = getHero();
    if (hero && hero.parentNode) {
      hero.insertAdjacentElement('afterend', nav);
      return;
    }
    var main = document.querySelector('main');
    if (main && main.parentNode) main.parentNode.insertBefore(nav, main);
    else document.body.insertBefore(nav, document.body.firstChild);
  }

  function cleanHash() {
    if (!window.location.hash || !window.history || !window.history.replaceState) return;
    window.history.replaceState(window.history.state, '', window.location.pathname + window.location.search);
  }

  function setupNav() {
    addStyles();
    var links = getSectionLinks();
    var existing = findExistingNav();
    if (!links.length && !existing) return;
    var nav = normalizeExistingNav(existing, links);
    if (!nav.isConnected) insertAfterHero(nav);
    else {
      var hero = getHero();
      if (hero && nav.previousElementSibling !== hero && !nav.classList.contains('is-floating')) {
        hero.insertAdjacentElement('afterend', nav);
      }
    }
    nav.querySelectorAll('nav a[href^="#"]').forEach(function (a) {
      var id = a.getAttribute('data-cd-section-id') || decodeURIComponentSafe((a.getAttribute('href') || '').slice(1));
      var target = document.getElementById(id);
      if (target) target.classList.add('cd-onpage-target');
    });
    setupVisibility(nav);
  }

  function setupVisibility(nav) {
    var hero = getHero();
    if (!hero || !('IntersectionObserver' in window)) {
      nav.classList.add('is-visible');
      return;
    }
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        nav.classList.toggle('is-visible', !entry.isIntersecting && entry.boundingClientRect.bottom <= 0);
      });
    }, { threshold: 0 });
    observer.observe(hero);
    nav.classList.remove('is-visible');
  }

  document.addEventListener('click', function (event) {
    var link = event.target && event.target.closest ? event.target.closest('.cd-mobile-on-page-v2 a[href^="#"]') : null;
    if (!link) return;
    var id = link.getAttribute('data-cd-section-id') || decodeURIComponentSafe(link.getAttribute('href').slice(1));
    var target = document.getElementById(id);
    if (!target) return;
    event.preventDefault();
    target.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' });
    cleanHash();
    var details = link.closest('details');
    if (details) details.open = false;
  }, true);

  document.addEventListener('click', function (event) {
    if (!event.target.closest || event.target.closest('.cd-mobile-on-page-v2')) return;
    var summary = document.querySelector('.cd-mobile-on-page-v2 details[open]');
    if (summary) summary.open = false;
  });

  window.addEventListener('hashchange', cleanHash);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', setupNav, { once: true });
  else setupNav();
  cleanHash();
})();