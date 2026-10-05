(function(){
'use strict';

var PATH = window.location.pathname.replace(/\/$/,'');
var EXCLUDED = PATH === '' || PATH === '/' || PATH === '/index.html' ||
               PATH === '/collegedecoded-team' || PATH === '/about-us' ||
               PATH === '/about-us.html' || PATH === '/about' || PATH === '/about.html';
if (EXCLUDED) return;
if (window.__CD_COLLEGE_GUIDANCE_TEST) return;
window.__CD_COLLEGE_GUIDANCE_TEST = true;

function track(name, params){
  try{
    if (typeof window.gtag === 'function') window.gtag('event', name, params || {});
  }catch(e){}
}

function esc(s){
  return String(s || '').replace(/[&<>"']/g,function(c){
    return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
  });
}

function getCollegeName(){
  var h1 = document.querySelector('h1');
  var text = h1 ? (h1.textContent || '').trim() : (document.title || '').split('|')[0].trim();
  text = text.replace(/^CollegeDecoded\s*[|:-]\s*/i,'').trim();
  text = text.replace(/\s+(MBA|PGDM|Admission|Fees|Cutoff|Placements|Placement|Eligibility|Courses|Course).*$/i,'').trim();
  return text || 'this college';
}

function getPageContext(){
  var title=(document.title||'').toLowerCase();
  var body=(document.body.innerText||'').slice(0,5000).toLowerCase();
  var isMBA = /\bmba\b|\bpgdm\b|cat|xat|cmat|snap|nmat|mat/.test(title+' '+body);
  return {isMBA:isMBA};
}

function init(){
  if(document.getElementById('cdCollegeTestModal')) return;
  var hero=document.querySelector('.hero, .hero-section, .hero-container, header + section');
  var faq=document.getElementById('faq')||document.getElementById('faqs');
  if(!faq){
    var candidates=[].slice.call(document.querySelectorAll('section, .section, .main-section, .section-card, main > div'));
    for(var i=0;i<candidates.length;i++){
      var h=candidates[i].querySelector('h2,h3');
      var t=h?(h.textContent||'').toLowerCase():'';
      if(t.indexOf('frequently asked')!==-1 || /^faqs?$/.test(t.trim())){faq=candidates[i];break;}
    }
  }
  if(!faq) faq=document.querySelector('footer');
  if(!hero) hero=document.querySelector('main')||document.body;
  if(!faq) return;

  var college=getCollegeName();
  var ctx=getPageContext();
  var mba=ctx.isMBA;

  var modal=document.createElement('div');
  modal.id='cdCollegeTestModal';
  modal.className='cd-college-test-modal';
  modal.setAttribute('aria-hidden','true');

  var headline=mba ? 'Check Your '+college+' Admission Chances' : 'Get Personalised Admission Guidance';
  var sub=mba
    ? 'Share a few details and we’ll help you understand your chances, fees and alternatives.'
    : 'Tell us what you’re looking for and we’ll help you compare suitable college options.';
  var leftTitle=mba ? 'Your MBA Journey, Simplified' : 'Your College Search, Simplified';

  modal.innerHTML =
    '<div class="cd-college-test-backdrop"></div>'+
    '<div class="cd-college-test-dialog" role="dialog" aria-modal="true" aria-labelledby="cdCollegeTestTitle">'+
      '<button class="cd-college-test-close" type="button" aria-label="Close">×</button>'+
      '<div class="cd-college-test-grid">'+
        '<aside class="cd-college-test-left">'+
          '<div>'+
            '<div class="cd-college-test-brand">College<span>Decoded</span></div>'+
            '<h3>'+esc(leftTitle)+'</h3>'+
            '<p>Tell us what you need. We’ll help you make a more realistic shortlist based on your profile, goals and budget.</p>'+
            '<div class="cd-college-test-points">'+
              '<div class="cd-college-test-point"><i>✓</i>Personalised college recommendations</div>'+
              '<div class="cd-college-test-point"><i>✓</i>Guidance on cutoffs, fees & eligibility</div>'+
              '<div class="cd-college-test-point"><i>✓</i>Compare suitable alternatives</div>'+
              '<div class="cd-college-test-point"><i>✓</i>Free and no obligation</div>'+
            '</div>'+
          '</div>'+
          '<div class="cd-college-test-trust">Free guidance • No obligation</div>'+
        '</aside>'+
        '<div class="cd-college-test-right">'+
          '<div class="cd-college-test-progress"><span></span></div>'+
          '<h2 id="cdCollegeTestTitle">'+esc(headline)+'</h2>'+
          '<p class="cd-college-test-sub">'+esc(sub)+'</p>'+
          '<form id="cdCollegeTestForm">'+
            '<div class="cd-college-test-section">'+
              '<label class="cd-college-test-label">What would you like help with?</label>'+
              '<div class="cd-college-test-choices">'+
                '<label class="cd-college-test-choice"><input type="radio" name="interest" value="Check admission chances" required><span>🎯 Check my admission chances</span></label>'+
                '<label class="cd-college-test-choice"><input type="radio" name="interest" value="Build college shortlist"><span>📋 Build my college shortlist</span></label>'+
                '<label class="cd-college-test-choice"><input type="radio" name="interest" value="Find good ROI colleges"><span>📊 Find colleges with good ROI</span></label>'+
                '<label class="cd-college-test-choice"><input type="radio" name="interest" value="Not sure"><span>🤔 Not sure yet</span></label>'+
              '</div>'+
            '</div>'+
            '<div class="cd-college-test-section">'+
              '<label class="cd-college-test-label">College you’re exploring</label>'+
              '<div class="cd-college-test-current-college"><span>🏛️</span><strong>'+esc(college)+'</strong><em>From this page</em></div>'+
            '</div>'+
            '<div class="cd-college-test-fields">'+
              '<div class="cd-college-test-field"><label>Entrance exam <em>(optional)</em></label><select name="exam"><option value="">Select</option><option>CAT</option><option>XAT</option><option>CMAT</option><option>MAT</option><option>SNAP</option><option>NMAT</option><option>Other</option><option>Not appeared yet</option></select></div>'+
              '<div class="cd-college-test-field"><label>Expected score/percentile <em>(optional)</em></label><input name="score" inputmode="decimal" placeholder="e.g. 95 percentile"></div>'+
              '<div class="cd-college-test-field"><label>Budget <em>(optional)</em></label><select name="budget"><option value="">Select</option><option>Under ₹5L</option><option>₹5–10L</option><option>₹10–20L</option><option>₹20L+</option><option>Not sure</option></select></div>'+
              '<div class="cd-college-test-field"><label>Category <em>(optional)</em></label><select name="category"><option value="">Select</option><option>General</option><option>OBC</option><option>SC</option><option>ST</option><option>EWS</option><option>Prefer not to say</option></select></div>'+
            '</div>'+
            '<div class="cd-college-test-section">'+
              '<label class="cd-college-test-label">Where should we send your guidance?</label>'+
              '<div class="cd-college-test-fields cd-contact-fields">'+
                '<div class="cd-college-test-field"><label>Name</label><input name="name" autocomplete="name" required placeholder="Your name"></div>'+
                '<div class="cd-college-test-field"><label>Mobile number</label><input name="mobile" autocomplete="tel" inputmode="numeric" required placeholder="+91 98XXXXXXXX" pattern="[0-9+() -]{10,16}"></div>'+
                '<div class="cd-college-test-field cd-email-field"><label>Email <em>(optional)</em></label><input name="email" autocomplete="email" type="email" placeholder="you@example.com"></div>'+
              '</div>'+
            '</div>'+
            '<label class="cd-college-test-consent"><input type="checkbox" name="consent" required><span>I agree to be contacted by CollegeDecoded for admission guidance. We won’t share your details with third parties.</span></label>'+
            '<button class="cd-college-test-submit" type="submit">Get My Free Guidance <span>→</span></button>'+
            '<div class="cd-college-test-note">Your details are used only to respond to this guidance request.</div>'+
          '</form>'+
        '</div>'+
      '</div>'+
    '</div>';

  document.body.appendChild(modal);

  var section=document.createElement('section');
  section.id='cdCollegeTestGuidanceSection';
  section.className='cd-college-test-guidance';
  section.innerHTML='<div><h2>Not sure which college is right for you?</h2><p>Tell us your exam, score and budget. We’ll help you explore suitable options and alternatives.</p></div><button type="button">Get Free Guidance →</button>';
  faq.parentNode.insertBefore(section,faq);

  var form=modal.querySelector('#cdCollegeTestForm');
  var endpoint='https://script.google.com/macros/s/AKfycbwfyXmhmRd5yB5QJL7ZuCvHhC3PjldwMQlD6f-HmzrOez_gUfzA0vga-UwQHrKPlXvp/exec';

  function open(reason){
    modal.classList.add('cd-iima-open');
    modal.setAttribute('aria-hidden','false');
    document.body.style.overflow='hidden';
    track('guidance_form_open',{page_path:location.pathname, college:college, trigger:reason||'cta'});
  }
  function close(){
    modal.classList.remove('cd-iima-open');
    modal.setAttribute('aria-hidden','true');
    document.body.style.overflow='';
  }

  modal.querySelector('.cd-college-test-close').addEventListener('click',close);
  modal.querySelector('.cd-college-test-backdrop').addEventListener('click',close);
  document.addEventListener('keydown',function(e){
    if(e.key==='Escape' && modal.classList.contains('cd-iima-open')) close();
  });

  var started=false;
  function markStart(){
    if(started)return;
    started=true;
    track('form_start',{page_path:location.pathname,college:college});
  }
  form.addEventListener('focusin',markStart);

  form.addEventListener('submit',function(e){
    e.preventDefault();
    if(!form.reportValidity())return;
    markStart();
    var btn=form.querySelector('.cd-college-test-submit');
    btn.disabled=true;
    btn.innerHTML='Submitting…';

    var data={
      source_page:window.location.href,
      page_title:document.title,
      college:college,
      interest:(form.querySelector('input[name="interest"]:checked')||{}).value||'',
      exam:form.exam.value,
      score:form.score.value,
      budget:form.budget.value,
      category:form.category.value,
      name:form.name.value,
      mobile:form.mobile.value,
      email:form.email.value,
      consent:form.consent.checked ? 'Yes' : 'No'
    };

    var body=new URLSearchParams(data);
    fetch(endpoint,{method:'POST',mode:'no-cors',body:body,keepalive:true})
      .then(function(){
        track('generate_lead',{page_path:location.pathname,college:college,lead_source:'guidance_form'});
        try{sessionStorage.setItem('CD_CollegeDecoded_GUIDANCE_HANDLED','1')}catch(err){}
        form.innerHTML='<div class="cd-college-test-success"><div class="cd-success-icon">✓</div><h2>You’re all set!</h2><p>Your guidance request has been submitted successfully. We’ll use the details you shared to help you explore your options.</p><button type="button" class="cd-college-test-continue">Continue exploring</button></div>';
        form.querySelector('.cd-college-test-continue').addEventListener('click',close);
      })
      .catch(function(){
        btn.disabled=false;
        btn.innerHTML='Get My Free Guidance <span>→</span>';
        alert('We could not submit your request. Please try again.');
      });
  });

  var triggered=false;
  function checkScroll(){
    if(triggered)return;
    var heroBottom=hero.getBoundingClientRect().bottom+window.pageYOffset;
    var past=Math.max(0,(window.pageYOffset||0)-heroBottom);
    if(Math.floor(past/500)>=3){
      triggered=true;
      var handled=false;
      try{handled=sessionStorage.getItem('CD_CollegeDecoded_GUIDANCE_HANDLED')==='1'}catch(e){}
      if(!handled) open('scroll');
    }
  }
  window.addEventListener('scroll',checkScroll,{passive:true});

  section.querySelector('button').addEventListener('click',function(e){
    e.preventDefault();
    open('cta');
  });

  document.addEventListener('click',function(e){
    var target=e.target.closest ? e.target.closest('#cdCollegeTestGuidanceSection button') : null;
    if(target){e.preventDefault();open('cta');}
  });
}

if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',init);
else init();
})();