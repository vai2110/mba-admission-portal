(function(){
'use strict';
if(window.__CD_GUIDANCE_READY)return;
window.__CD_GUIDANCE_READY=true;

function init(){
  if(document.getElementById('cdGuidanceModal'))return;

  var cta=document.createElement('section');
  cta.className='cd-guidance-cta';
  cta.innerHTML='<div><strong>🎓 Confused about your college options?</strong><p>Get personalised guidance based on what you are looking for.</p></div><button type="button" class="cd-guidance-open">Get Free Guidance →</button>';

  var container=document.querySelector('main .content')||document.querySelector('main');
  if(container){
    var sections=container.querySelectorAll(':scope > section');
    if(sections.length>=3) sections[2].insertAdjacentElement('afterend',cta);
    else if(sections.length>=1) sections[sections.length-1].insertAdjacentElement('afterend',cta);
    else container.appendChild(cta);
  }else{
    document.body.appendChild(cta);
  }

  var modal=document.createElement('div');
  modal.id='cdGuidanceModal';
  modal.className='cd-guidance-modal';
  modal.setAttribute('aria-hidden','true');
  modal.innerHTML='<div class="cd-guidance-backdrop"></div>'+
  '<div class="cd-guidance-dialog" role="dialog" aria-modal="true" aria-labelledby="cdGuidanceTitle">'+
  '<button type="button" class="cd-guidance-close" aria-label="Close">×</button>'+
  '<div class="cd-guidance-head"><div><h2 id="cdGuidanceTitle">🎓 Confused about your college options?</h2><p>Tell us what you are looking for. We will help you explore your options.</p></div><div class="cd-guidance-badge">FREE GUIDANCE</div></div>'+
  '<form class="cd-guidance-form" id="cdGuidanceForm">'+
  '<div class="cd-guidance-field cd-full"><label>What are you looking for?</label><div class="cd-choice-row">'+
  '<label class="cd-choice"><input type="radio" name="interest" value="MBA / PGDM" required><span>MBA / PGDM</span></label>'+
  '<label class="cd-choice"><input type="radio" name="interest" value="Engineering"><span>Engineering</span></label>'+
  '<label class="cd-choice"><input type="radio" name="interest" value="Medical"><span>Medical</span></label>'+
  '<label class="cd-choice"><input type="radio" name="interest" value="Other"><span>Other</span></label></div></div>'+
  '<div class="cd-guidance-field"><label>Exam &amp; Score <em>(optional)</em></label><input name="score" type="text" placeholder="e.g. CAT – 95 percentile"></div>'+
  '<div class="cd-guidance-field"><label>What do you need help with?</label><select name="help" required><option value="">Select one</option><option>Find colleges</option><option>Compare colleges</option><option>Admission guidance</option><option>Fees & placements</option><option>Not sure</option></select></div>'+
  '<div class="cd-guidance-field"><label>WhatsApp Number</label><input name="whatsapp" type="tel" inputmode="numeric" placeholder="+91 98XXXXXXXX" pattern="[0-9+() -]{10,16}" required></div>'+
  '<div class="cd-guidance-field"><label>Your Name</label><input name="name" type="text" placeholder="Your name" required></div>'+
  '<input type="hidden" name="source_page">'+
  '<button class="cd-guidance-submit" type="submit">Get Free Guidance →</button></form>'+
  '<div class="cd-guidance-note">We only use these details to respond to your guidance request. No spam.</div>'+
  '<div class="cd-guidance-success">Thanks! Your guidance request has been recorded for testing.</div></div>';
  document.body.appendChild(modal);

  var form=document.getElementById('cdGuidanceForm');
  form.elements.source_page.value=window.location.href;
  var shown=false;
  var scrollHits=0;
  var key='CD_GUIDANCE_SHOWN_V2:'+window.location.pathname;

  function wasShown(){try{return sessionStorage.getItem(key)==='1';}catch(e){return false;}}
  function markShown(){try{sessionStorage.setItem(key,'1');}catch(e){}}

  function show(force){
    if(!force&&(shown||wasShown()))return;
    shown=true; markShown();
    modal.classList.add('cd-open');
    modal.style.display='flex';
    modal.setAttribute('aria-hidden','false');
    document.body.style.overflow='hidden';
  }
  function close(){
    modal.classList.remove('cd-open');
    modal.style.display='none';
    modal.setAttribute('aria-hidden','true');
    document.body.style.overflow='';
    markShown();
  }

  cta.querySelector('.cd-guidance-open').addEventListener('click',function(){show(true);});
  modal.querySelector('.cd-guidance-close').addEventListener('click',close);
  modal.querySelector('.cd-guidance-backdrop').addEventListener('click',close);
  document.addEventListener('keydown',function(e){if(e.key==='Escape'&&modal.classList.contains('cd-open'))close();});

  form.addEventListener('submit',function(e){
    e.preventDefault();
    if(!form.checkValidity()){form.reportValidity();return;}
    modal.querySelector('.cd-guidance-success').style.display='block';
  });

  var lastY=window.pageYOffset||document.documentElement.scrollTop||0;
  function check(){
    if(shown||wasShown())return;
    var y=window.pageYOffset||document.documentElement.scrollTop||0;
    var delta=Math.abs(y-lastY);
    lastY=y;
    if(delta>=140)scrollHits++;
    var max=Math.max(1,document.documentElement.scrollHeight-window.innerHeight);
    var mobile=window.innerWidth<=640;
    var depth=mobile?0.45:0.40;
    if(scrollHits>=3 || (y/max)>=depth)show(false);
  }
  window.addEventListener('scroll',check,{passive:true});
  window.addEventListener('touchend',check,{passive:true});
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();