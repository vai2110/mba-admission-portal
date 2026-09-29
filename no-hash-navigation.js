(function () {
  'use strict';

  function cleanUrl() {
    if (window.location.hash) {
      window.history.replaceState(null, '', window.location.pathname + window.location.search);
    }
  }

  function handleAnchorClick(event) {
    var link = event.target.closest && event.target.closest('a[href]');
    if (!link || event.defaultPrevented) return;

    var raw = link.getAttribute('href') || '';
    if (!raw || raw.charAt(0) !== '#') return;

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

    // Remove the fragment immediately so it never remains visible in the address/search bar.
    cleanUrl();
  }

  // Capture phase also covers navigation links handled by nested buttons/dropdowns.
  document.addEventListener('click', handleAnchorClick, true);

  // Remove fragments added by browser navigation, redirects or other scripts.
  window.addEventListener('hashchange', cleanUrl);

  // Remove any fragment present on initial page load.
  cleanUrl();
})();
