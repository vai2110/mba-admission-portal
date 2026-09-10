document.addEventListener('DOMContentLoaded', function () {
  // Mobile "On this page" menu: close it after a section link is selected.
  document.querySelectorAll('.mobile-on-page details a[href^="#"]').forEach(function (link) {
    link.addEventListener('click', function () {
      var details = link.closest('details');
      if (details) details.removeAttribute('open');
    });
  });

  // FAQ accordion: one open answer at a time, keyboard accessible.
  document.querySelectorAll('#faq .faq-item').forEach(function (item, index) {
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

    function toggle() {
      var isOpen = item.classList.contains('open');
      document.querySelectorAll('#faq .accordion-item.open').forEach(function (other) {
        if (other !== item) {
          other.classList.remove('open');
          var q = other.querySelector('.accordion-question');
          var a = other.querySelector('.accordion-answer');
          if (q) q.setAttribute('aria-expanded', 'false');
          if (a) a.setAttribute('aria-hidden', 'true');
        }
      });
      item.classList.toggle('open', !isOpen);
      question.setAttribute('aria-expanded', String(!isOpen));
      answer.setAttribute('aria-hidden', String(isOpen));
    }

    question.addEventListener('click', toggle);
    question.addEventListener('keydown', function (event) {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        toggle();
      }
    });
  });
});
