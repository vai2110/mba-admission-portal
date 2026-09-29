(function () {
  'use strict';

  function cleanUrl() {
    if (window.location.hash) {
      window.history.replaceState(null, '', window.location.pathname + window.location.search);
    }
  }

  function handleAnchorClick(event) {
    var link = event.target.closest && event.target.closest('a[href^="#"]');
    if (!link || event.defaultPrevented) return;

    var raw = link.getAttribute('href') || '';
    var id = raw.slice(1);

    if (!id) {
      event.preventDefault();
      cleanUrl();
      return;
    }

    var target;
    try {
      target = document.getElementById(decodeURIComponent(id));
    } catch (e) {
      target = document.getElementById(id);
    }

    if (!target) return;

    event.preventDefault();
    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    window.setTimeout(cleanUrl, 0);
  }

  document.addEventListener('click', handleAnchorClick, true);

  window.addEventListener('hashchange', function () {
    window.setTimeout(cleanUrl, 0);
  });

  window.addEventListener('load', function () {
    if (window.location.hash) window.setTimeout(cleanUrl, 0);
  });
})();