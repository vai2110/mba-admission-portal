document.addEventListener('DOMContentLoaded', function () {
  // Keep the mobile On This Page dropdown folded after a section is selected.
  document.querySelectorAll('.mobile-on-page details a[href^="#"]').forEach(function (link) {
    link.addEventListener('click', function () {
      var details = link.closest('details');
      if (details) details.removeAttribute('open');
    });
  });

  // Shared FAQ accordion styling so every Chitkara page behaves consistently.
  var style = document.createElement('style');
  style.textContent = '.accordion-item{border:1px solid #dfe5ed;border-radius:8px;margin:10px 0;background:#fff;overflow:hidden}.accordion-question{position:relative;padding:15px 44px 15px 15px!important;margin:0!important;cursor:pointer;background:#f8fbff;color:#173f82!important;font-size:15px!important;font-weight:700}.accordion-question:after{content:"+";position:absolute;right:15px;top:50%;transform:translateY(-50%);font-size:22px;font-weight:400;color:#2563eb}.accordion-item.open .accordion-question{background:#eff6ff}.accordion-item.open .accordion-question:after{content:"−"}.accordion-answer{padding:14px 15px 16px!important;margin:0!important;color:#334155!important;font-size:13px!important;line-height:1.75!important}.accordion-question:focus-visible{outline:2px solid #2563eb;outline-offset:-2px}@media(max-width:720px){.accordion-question{font-size:14px!important;padding:13px 40px 13px 13px!important}.accordion-answer{font-size:13px!important;padding:12px 13px 14px!important}}';
  document.head.appendChild(style);

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
          if (a) {
            a.setAttribute('aria-hidden', 'true');
            a.hidden = true;
          }
        }
      });
      item.classList.toggle('open', !isOpen);
      question.setAttribute('aria-expanded', String(!isOpen));
      answer.setAttribute('aria-hidden', String(isOpen));
      answer.hidden = isOpen;
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
