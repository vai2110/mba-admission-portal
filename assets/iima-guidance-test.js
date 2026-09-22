(function(){
'use strict';
if(window.__CD_IIMA_GUIDANCE_TEST)return;
window.__CD_IIMA_GUIDANCE_TEST=true;

function init(){
  if(document.getElementById('cdIimaTestModal'))return;
  var hero=document.querySelector('.hero');
  var faq=document.getElementById('faq');
  if(!hero)return;

  function esc(s){return String(s||'').replace(/[&<>"']/g,function(c){return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]);});}

  var modal=document.createElement('div');
  modal.id='cdIimaTestModal';
  modal.className='cd-iima-test-modal';
  modal.setAttribute('aria-hidden','true');
  modal.innerHTML=
  '<div class="cd-iima-test-backdrop"></div>'+
  '<div class="cd-iima-test-dialog" role="dialog" aria-modal="true" aria-labelledby="cdIimaTestTitle">'+
    '<button class="cd-iima-test-close" type="button" aria-label="Close">×</button>'+
    '<div class="cd-iima-test-grid">'+
      '<div class="cd-iima-test-left">'+
        '<div>'+
          '<div class="cd-iima-test-brand">College<span>Decoded</span></div>'+
          '<h3>Your MBA Journey, Simplified</h3>'+
          '<p>Not sure which college is right for you? Tell us what you want — not just which page you landed on.</p>'+
          '<div class="cd-iima-test-points">'+
            '<div class="cd-iima-test-point"><i>✓</i>Personalised college recommendations</div>'+
            '<div class="cd-iima-test-point"><i>✓</i>Guidance on eligibility, cutoffs & fees</div>'+
            '<div class="cd-iima-test-point"><i>✓</i>Compare options based on your profile</div>'+
          '</div>'+
        '</div>'+
        '<div class="cd-iima-test-student" aria-hidden="true">'+
          '<svg viewBox="0 0 220 190" xmlns="http://www.w3.org/2000/svg">'+
            '<circle cx="112" cy="55" r="33" fill="#ffd0b5"/><path d="M78 55c2-29 27-45 56-31 13 6 21 19 19 34-11-7-21-14-29-24-7 13-20 20-46 21z" fill="#1e293b"/><path d="M90 66c8 6 20 7 31 2" fill="none" stroke="#9a4f3b" stroke-width="3" stroke-linecap="round"/><circle cx="99" cy="56" r="3" fill="#092653"/><circle cx="124" cy="56" r="3" fill="#092653"/><path d="M70 105c10-20 34-29 58-27 29 2 44 19 51 49l-7 42H58l-4-39c2-12 7-19 16-25z" fill="#174ea6"/><path d="M91 84l21 23 20-23" fill="#fff"/><path d="M91 84l21 23 20-23" fill="none" stroke="#dbeafe" stroke-width="2"/><path d="M70 122l-24 28" stroke="#ffd0b5" stroke-width="15" stroke-linecap="round"/><path d="M146 119l25 29" stroke="#ffd0b5" stroke-width="15" stroke-linecap="round"/><path d="M52 155l-13 27M164 153l15 29" stroke="#0f172a" stroke-width="13" stroke-linecap="round"/><path d="M33 183h31M165 182h31" stroke="#ff6b16" stroke-width="9" stroke-linecap="round"/><path d="M78 122c15 9 31 9 45 0" fill="none" stroke="#0b3d91" stroke-width="5"/></svg>'+
        '</div>'+
      '</div>'+
      '<div class="cd-iima-test-right">'+
        '<div class="cd-iima-test-progress"><span></span></div>'+
        '<h2 id="cdIimaTestTitle">Get Free MBA Guidance</h2>'+
        '<p class="cd-iima-test-sub">We’ll help you explore the right options based on your goals and preferences.</p>'+
        '<form id="cdIimaTestForm">'+
          '<div class="cd-iima-test-step active" data-step="1">'+
            '<label class="cd-iima-test-label">What are you looking for?</label>'+
            '<div class="cd-iima-test-choices">'+
              '<label class="cd-iima-test-choice"><input type="radio" name="iima_interest" value="Exploring MBA colleges"><span>🔎 I’m exploring MBA colleges</span></label>'+
              '<label class="cd-iima-test-choice"><input type="radio" name="iima_interest" value="Have colleges in mind"><span>🎯 I have some colleges in mind</span></label>'+
              '<label class="cd-iima-test-choice"><input type="radio" name="iima_interest" value="Targeting top MBA colleges"><span>🏆 I’m targeting top MBA colleges</span></label>'+
              '<label class="cd-iima-test-choice"><input type="radio" name="iima_interest" value="Good ROI"><span>💰 I want colleges with good ROI</span></label>'+
              '<label class="cd-iima-test-choice"><input type="radio" name="iima_interest" value="Based on CAT percentile"><span>📊 Based on my CAT percentile</span></label>'+
              '<label class="cd-iima-test-choice"><input type="radio" name="iima_interest" value="Not sure yet"><span>🤔 Not sure yet</span></label>'+
            '</div>'+
            '<label class="cd-iima-test-label">Which colleges are you considering? <small>(optional — landing here doesn’t mean you’ve chosen IIM Ahmedabad)</small></label>'+
            '<div class="cd-iima-test-tags" id="cdIimaCollegeTags">'+
              '<button type="button" class="cd-iima-test-tag selected" data-college="IIM Ahmedabad">IIM Ahmedabad ×</button>'+
              '<button type="button" class="cd-iima-test-tag" data-college="IIM Bangalore">IIM Bangalore</button>'+
              '<button type="button" class="cd-iima-test-tag" data-college="IIM Calcutta">IIM Calcutta</button>'+
              '<button type="button" class="cd-iima-test-tag" data-college="Not sure">Not sure</button>'+
            '</div>'+
            '<div class="cd-iima-test-actions"><button class="cd-iima-test-btn" type="button" data-next>Next →</button></div>'+
          '</div>'+
          '<div class="cd-iima-test-step" data-step="2">'+
            '<label class="cd-iima-test-label">A few details so we can personalise the guidance</label>'+
            '<div class="cd-iima-test-fields">'+
              '<div class="cd-iima-test-field"><label>Preferred location</label><select name="location"><option value="">Select</option><option>Delhi NCR</option><option>Mumbai</option><option>Bangalore</option><option>Ahmedabad</option><option>Any</option></select></div>'+
              '<div class="cd-iima-test-field"><label>Total fee budget</label><select name="budget"><option value="">Select</option><option>Under ₹5L</option><option>₹5–10L</option><option>₹10–20L</option><option>₹20L+</option><option>Not sure</option></select></div>'+
              '<div class="cd-iima-test-field"><label>Entrance exam</label><select name="exam"><option value="">Select</option><option>CAT</option><option>XAT</option><option>NMAT</option><option>SNAP</option><option>Other</option><option>Not appeared</option></select></div>'+
              '<div class="cd-iima-test-field"><label>CAT percentile (if any)</label><input name="percentile" inputmode="decimal" placeholder="e.g. 95"></div>'+
              '<div class="cd-iima-test-field"><label>Your name</label><input name="name" required placeholder="Enter your name"></div>'+
              '<div class="cd-iima-test-field"><label>Mobile number</label><input name="mobile" required inputmode="numeric" placeholder="+91 98XXXXXXXX" pattern="[0-9+() -]{10,16}"></div>'+
            '</div>'+
            '<div class="cd-iima-test-actions"><button class="cd-iima-test-btn cd-iima-test-back" type="button" data-back>← Back</button><button class="cd-iima-test-btn" type="submit">Get Free Guidance →</button></div>'+
            '<div class="cd-iima-test-note">No obligation • Quick response • Your details are used only for your guidance request.</div>'+
          '</div>'+
        '</form>'+
      '</div>'+
    '</div>'+
  '</div>';
  document.body.appendChild(modal);

  var floating=document.createElement('div');
  floating.className='cd-iima-test-floating';
  floating.innerHTML='<div><strong>Still exploring your MBA options?</strong></div><button type="button">Get Free Guidance</button>';
  document.body.appendChild(floating);

  if(faq && !document.getElementById('cdIimaTestGuidanceSection')){
    var section=document.createElement('section');
    section.id='cdIimaTestGuidanceSection';
    section.className='cd-iima-test-guidance';
    section.innerHTML='<div><h2>Not sure which MBA college is right for you?</h2><p>Tell us your exam, budget, location and goals. We’ll help you explore colleges — including alternatives to the college you’re currently viewing.</p></div><button type="button">Get Free Guidance →</button>';
    faq.parentNode.insertBefore(section,faq);
  }

  var form=document.getElementById('cdIimaTestForm');
  var steps=[].slice.call(modal.querySelectorAll('.cd-iima-test-step'));
  var progress=modal.querySelector('.cd-iima-test-progress span');
  var selectedColleges=['IIM Ahmedabad'];
  var currentStep=1;
  var source='IIM Ahmedabad page';
  try{sessionStorage.setItem('CD_IIMA_GUIDANCE_SOURCE',window.location.href)}catch(e){}

  function open(){
    modal.classList.add('cd-iima-open');modal.setAttribute('aria-hidden','false');
    document.body.style.overflow='hidden';
    floating.classList.remove('show');
  }
  function close(){
    modal.classList.remove('cd-iima-open');modal.setAttribute('aria-hidden','true');
    document.body.style.overflow='';
    if(scrolledEnough) floating.classList.add('show');
  }
  function goStep(n){
    currentStep=n;
    steps.forEach(function(s){s.classList.toggle('active',Number(s.getAttribute('data-step'))===n)});
    progress.style.width=n===1?'50%':'100%';
    modal.querySelector('.cd-iima-test-dialog').scrollTop=0;
  }

  modal.querySelector('.cd-iima-test-close').addEventListener('click',close);
  modal.querySelector('.cd-iima-test-backdrop').addEventListener('click',close);
  document.addEventListener('keydown',function(e){if(e.key==='Escape'&&modal.classList.contains('cd-iima-open'))close()});
  modal.querySelector('[data-next]').addEventListener('click',function(){
    if(!form.querySelector('input[name="iima_interest"]:checked')){alert('Please select what you are looking for.');return}
    goStep(2);
  });
  modal.querySelector('[data-back]').addEventListener('click',function(){goStep(1)});
  modal.querySelectorAll('.cd-iima-test-tag').forEach(function(tag){
    tag.addEventListener('click',function(){
      var college=tag.getAttribute('data-college');
      if(college==='Not sure'){selectedColleges=['Not sure'];modal.querySelectorAll('.cd-iima-test-tag').forEach(function(x){x.classList.remove('selected')});tag.classList.add('selected');return}
      if(selectedColleges.indexOf('Not sure')!==-1)selectedColleges=[];
      var idx=selectedColleges.indexOf(college);
      if(idx===-1){selectedColleges.push(college);tag.classList.add('selected')}else{selectedColleges.splice(idx,1);tag.classList.remove('selected')}
    });
  });
  form.addEventListener('submit',function(e){
    e.preventDefault();
    if(!form.reportValidity())return;
    var data={source_page:source,interest:(form.querySelector('input[name="iima_interest"]:checked')||{}).value||'',colleges:selectedColleges,location:form.location.value,budget:form.budget.value,exam:form.exam.value,percentile:form.percentile.value,name:form.name.value,mobile:form.mobile.value};
    try{sessionStorage.setItem('CD_IIMA_GUIDANCE_TEST_SUBMISSION',JSON.stringify(data));sessionStorage.setItem('CD_IIMA_GUIDANCE_HANDLED','1')}catch(err){}
    form.innerHTML='<div style="text-align:center;padding:45px 8px"><div style="font-size:42px">🎓</div><h2 style="color:#092653;margin:10px 0">You’re all set!</h2><p style="color:#64748b;font-size:13px">Your guidance preferences have been recorded for this test flow.</p><button type="button" class="cd-iima-test-btn" data-done>Continue exploring</button></div>';
    modal.querySelector('[data-done]').addEventListener('click',close);
  });

  var scrolledEnough=false,triggered=false,lastY=window.pageYOffset||0;
  function checkScroll(){
    if(triggered)return;
    var heroBottom=hero.getBoundingClientRect().bottom+window.pageYOffset;
    var past=Math.max(0,(window.pageYOffset||0)-heroBottom);
    var meaningful=Math.floor(past/500);
    if(meaningful>=3){
      scrolledEnough=true;triggered=true;
      var handled=false;try{handled=sessionStorage.getItem('CD_IIMA_GUIDANCE_HANDLED')==='1'}catch(e){}
      if(!handled)open();else floating.classList.add('show');
    }
  }
  window.addEventListener('scroll',checkScroll,{passive:true});
  modal.querySelector('.cd-iima-test-guidance button').addEventListener('click',open);
  floating.querySelector('button').addEventListener('click',open);
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();