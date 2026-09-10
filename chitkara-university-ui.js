document.addEventListener('DOMContentLoaded', function () {
  // Build the left sidebar from sections that actually exist on THIS page.
  // Use short, student-friendly labels instead of copying full H2 headings.
  var shortLabels = {
    overview: 'Overview',
    courses: 'Courses',
    admission: 'Admission',
    fees: 'Fees',
    placements: 'Placements',
    campus: 'Campus & Hostel',
    hostel: 'Hostel & Campus',
    fit: 'Who Should Apply',
    faq: 'FAQs',
    process: 'Admission Process',
    eligibility: 'Eligibility',
    engineering: 'Engineering Admission',
    documents: 'Documents',
    btech: 'B.Tech / B.E.',
    bba: 'BBA & B.Com',
    bcom: 'BBA & B.Com',
    mba: 'MBA',
    bca: 'BCA',
    scholarships: 'Scholarships',
    rankings: 'Rankings',
    reviews: 'Reviews',
    careers: 'Placements & Careers',
    recruiters: 'Top Recruiters',
    selection: 'Selection Process',
    curriculum: 'Curriculum',
    specializations: 'Specializations',
    eligibilitycriteria: 'Eligibility',
    fee: 'Fees',
    hostel: 'Hostel',
    facilities: 'Facilities',
    studentlife: 'Student Life'
  };

  document.querySelectorAll('.sidebar-card').forEach(function (card) {
    var main = document.querySelector('main.content');
    if (!main) return;
    var sections = Array.prototype.slice.call(main.querySelectorAll('.main-section[id]'));
    if (!sections.length) return;

    Array.prototype.slice.call(card.querySelectorAll('a')).forEach(function (link) { link.remove(); });

    sections.forEach(function (section) {
      var heading = section.querySelector('h2');
      if (!heading) return;
      var link = document.createElement('a');
      link.href = '#' + section.id;
      var key = section.id.toLowerCase().replace(/[^a-z0-9]/g, '');
      link.textContent = shortLabels[key] || heading.textContent.trim().replace(/\s+/g, ' ').replace(/\s+2026\b/gi, '').replace(/:\s*.+$/, '');
      link.className = 'sidebar-section-link';
      card.appendChild(link);
    });
  });

  // Keep mobile On This Page folded after selecting a section.
  document.querySelectorAll('.mobile-on-page details a[href^="#"]').forEach(function (link) {
    link.addEventListener('click', function () {
      var details = link.closest('details');
      if (details) details.removeAttribute('open');
    });
  });

  // Shared FAQ accordion styling.
  var style = document.createElement('style');
  style.textContent = '.accordion-item{border:1px solid #dfe5ed;border-radius:8px;margin:10px 0;background:#fff;overflow:hidden}.accordion-question{position:relative;padding:15px 44px 15px 15px!important;margin:0!important;cursor:pointer;background:#f8fbff;color:#173f82!important;font-size:15px!important;font-weight:700}.accordion-question:after{content:"+";position:absolute;right:15px;top:50%;transform:translateY(-50%);font-size:22px;font-weight:400;color:#2563eb}.accordion-item.open .accordion-question{background:#eff6ff}.accordion-item.open .accordion-question:after{content:"−"}.accordion-answer{padding:14px 15px 16px!important;margin:0!important;color:#334155!important;font-size:13px!important;line-height:1.75!important}.accordion-question:focus-visible{outline:2px solid #2563eb;outline-offset:-2px}.sidebar-section-link{display:block!important}.sidebar-section-link.active{font-weight:700;background:#eff6ff;color:#1d4ed8}@media(max-width:720px){.accordion-question{font-size:14px!important;padding:13px 40px 13px 13px!important}.accordion-answer{font-size:13px!important;padding:12px 13px 14px!important}}';
  document.head.appendChild(style);

  // Highlight the sidebar section currently in view.
  var sidebarLinks = Array.prototype.slice.call(document.querySelectorAll('.sidebar-section-link'));
  var observedSections = sidebarLinks.map(function (link) {
    return document.getElementById(link.getAttribute('href').slice(1));
  }).filter(Boolean);
  if ('IntersectionObserver' in window && observedSections.length) {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          sidebarLinks.forEach(function (link) { link.classList.remove('active'); });
          var active = document.querySelector('.sidebar-section-link[href="#' + entry.target.id + '"]');
          if (active) active.classList.add('active');
        }
      });
    }, { rootMargin: '-15% 0px -70% 0px', threshold: 0 });
    observedSections.forEach(function (section) { observer.observe(section); });
  }

  // FAQ accordion: one answer open at a time, with keyboard support.
  document.querySelectorAll('#faq .faq-item').forEach(function (item) {
    var question = item.querySelector('h3');
    var answer = item.querySelector('p');
    if (!question || !answer) return;
    item.classList.add('accordion-item');
    question.classList.add('accordion-question');
    answer.classList.add('accordion-answer');
    question.setAttribute('role', 'button');
    question.setAttribute('tabindex', '0');
    question.setAttribute('aria-expanded', 'false');
    answer.setAttribute('aria-hidden', 'true');
    answer.hidden = true;

    function toggle() {
      var isOpen = item.classList.contains('open');
      document.querySelectorAll('#faq .accordion-item.open').forEach(function (other) {
        if (other !== item) {
          other.classList.remove('open');
          var q = other.querySelector('.accordion-question');
          var a = other.querySelector('.accordion-answer');
          if (q) q.setAttribute('aria-expanded', 'false');
          if (a) { a.setAttribute('aria-hidden', 'true'); a.hidden = true; }
        }
      });
      item.classList.toggle('open', !isOpen);
      question.setAttribute('aria-expanded', String(!isOpen));
      answer.setAttribute('aria-hidden', String(isOpen));
      answer.hidden = isOpen;
    }
    question.addEventListener('click', toggle);
    question.addEventListener('keydown', function (event) {
      if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); toggle(); }
    });
  });
});
