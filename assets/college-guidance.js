(function(){
'use strict';
if(window.__CD_GUIDANCE_GATE_READY)return;
window.__CD_GUIDANCE_GATE_READY=true;

function init(){
  if(document.getElementById('cdGuidanceGate'))return;

  var main=document.querySelector('main .content')||document.querySelector('main');
  if(!main)return;

  var sections=Array.prototype.slice.call(main.querySelectorAll(':scope > section'));
  if(sections.length<6)return;

  var meaningfulScrolls=0,lastY=window.pageYOffset||document.documentElement.scrollTop||0;
  var gated=false;
  var key='CD_GUIDANCE_GATE:'+window.location.pathname;

  function wasHandled(){
    try{return sessionStorage.getItem(key)==='1';}catch(e){return false;}
  }
  function markHandled(){
    try{sessionStorage.setItem(key,'1');}catch(e){}
  }

  function createGate(){
    if(gated||wasHandled())return;

    var currentY=window.pageYOffset||document.documentElement.scrollTop||0;
    var viewportBottom=currentY+window.innerHeight;
    var target=null;

    for(var i=0;i<sections.length;i++){
      var rect=sections[i].getBoundingClientRect();
      var top=rect.top+currentY;
      if(top>viewportBottom-80){target=sections[i];break;}
    }

    if(!target){
      for(var j=0;j<sections.length;j++){
        if(sections[j].getBoundingClientRect().top+currentY>currentY+window.innerHeight*0.45){
          target=sections[j];break;
        }
      }
    }

    if(!target)return;

    var gate=document.createElement('section');
    gate.id='cdGuidanceGate';
    gate.className='cd-guidance-gate';
    gate.innerHTML=
      '<div class="cd-gate-inner">'+
      '<div class="cd-gate-icon">🎓</div>'+
      '<h2>Want help choosing the right college?</h2>'+
      '<p>You have explored the key details. Get personalised guidance based on your course, exam score and goals — or continue reading the full guide.</p>'+
      '<div class="cd-gate-actions">'+
      '<button type="button" class="cd-gate-guidance">Get Free Guidance →</button>'+
      '<button type="button" class="cd-gate-continue">Continue Reading →</button>'+
      '</div></div>';

    target.parentNode.insertBefore(gate,target);

    var hidden=[];
    var node=gate.nextElementSibling;
    while(node){
      if(node!==gate){
        hidden.push(node);
        node.classList.add('cd-gated-content');
        node.setAttribute('aria-hidden','true');
      }
      node=node.nextElementSibling;
    }

    var modal=document.createElement('div');
    modal.id='cdGuidanceModal';
    modal.className='cd-guidance-modal';
    modal.setAttribute('aria-hidden','true');
    modal.innerHTML=
      '<div class="cd-guidance-backdrop"></div>'+
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

    function openModal(){
      modal.classList.add('cd-open');
      modal.style.display='flex';
      modal.setAttribute('aria-hidden','false');
      document.body.style.overflow='hidden';
    }
    function closeModal(){
      modal.classList.remove('cd-open');
      modal.style.display='none';
      modal.setAttribute('aria-hidden','true');
      document.body.style.overflow='';
    }

    gate.querySelector('.cd-gate-guidance').addEventListener('click',openModal);
    gate.querySelector('.cd-gate-continue').addEventListener('click',function(){
      hidden.forEach(function(el){
        el.classList.remove('cd-gated-content');
        el.removeAttribute('aria-hidden');
      });
      gate.remove();
      closeModal();
      markHandled();
    });

    modal.querySelector('.cd-guidance-close').addEventListener('click',closeModal);
    modal.querySelector('.cd-guidance-backdrop').addEventListener('click',closeModal);
    document.addEventListener('keydown',function(e){
      if(e.key==='Escape'&&modal.classList.contains('cd-open'))closeModal();
    });

    form.addEventListener('submit',function(e){
      e.preventDefault();
      if(!form.checkValidity()){form.reportValidity();return;}
      modal.querySelector('.cd-guidance-success').style.display='block';
    });

    gated=true;
    markHandled();
  }

  function checkScroll(){
    if(gated||wasHandled())return;
    var y=window.pageYOffset||document.documentElement.scrollTop||0;
    var delta=Math.abs(y-lastY);
    lastY=y;
    if(delta>=140)meaningfulScrolls++;
    if(meaningfulScrolls>=5)createGate();
  }

  window.addEventListener('scroll',checkScroll,{passive:true});
  window.addEventListener('touchend',checkScroll,{passive:true});
}

if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);
else init();
})();